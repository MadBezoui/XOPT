#!/usr/bin/env python3
"""Fail-closed local publication checks. Never uploads or changes Git references."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = "experiments/docs/publication_allowlist.json"
RELEASE_MANIFEST = "experiments/release_manifest.json"
SNAPSHOT_OBJECTS = {
    "experiments/provenance/objects/": "experiments/provenance/frozen_manifest.json",
    "experiments/provenance/corrections_20261024/objects/": "experiments/provenance/corrections_20261024/manifest.json",
}
FORBIDDEN_SUFFIXES = {
    ".tex", ".ltx", ".bib", ".bbl", ".bst", ".cls", ".sty", ".clo",
    ".doc", ".docx", ".docm", ".dot", ".dotx", ".dotm", ".odt", ".ott", ".rtf", ".typ", ".qmd", ".rmd",
    ".svg", ".eps", ".ai", ".psd", ".indd", ".pages", ".pgf", ".tikz", ".fig",
    ".aux", ".toc", ".out", ".synctex", ".spl", ".part", ".dtx", ".ins", ".bbx", ".cbx", ".lbx", ".lco", ".drawio",
}
PRIVATE_PARTS = {"article", "manuscript", "manuscripts", "templates", "tables", "figures",
                 ".git", ".venv", "__pycache__", "local_work", "superseded", "research"}
PRIVATE_FILENAMES = {"author_signoff.md", "correction_plan_20261024.md", "research_log.md",
                     "implementation_plan.md", "scientific_audit.md", "code_review.md", "design.md",
                     "resources_20261017.json"}
PRIVATE_PATHS = {f"experiments/results/levers_logs/bench_w{i}.log" for i in range(1, 7)}
PERSONAL_PATH = re.compile(rb"/(?:Users|home)/[^/\s'\"<>]+/|/private/var/" + b"folders/")
OPAQUE_ARCHIVE_SUFFIXES = {".gz", ".tgz", ".tar", ".bz2", ".xz", ".7z", ".rar", ".bundle"}
MAX_ARCHIVE_DEPTH = 5
MAX_EXPANDED_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 30000
MANUSCRIPT_CONTENT = re.compile(
    rb"(?m)^\s*(?:\\(?:documentclass|usepackage|bibliography|newcommand|renewcommand|providecommand)\s*\{|"
    rb"\\begin\s*\{(?:document|tabular|tabularx|longtable|table|figure|tikzpicture)\}|<svg(?:\s|>)|"
    rb"@(?:article|book|inproceedings|incollection|phdthesis|misc)\s*\{)", re.IGNORECASE)


class PolicyError(ValueError):
    """A local distribution would cross the publication boundary."""


def safe_path(name, *, package_member=False):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise PolicyError(f"unsafe path: {name!r}")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise PolicyError(f"absolute path: {name!r}")
    if any(part in {"", ".", ".."} for part in name.split("/")):
        raise PolicyError(f"noncanonical or traversal path: {name!r}")
    if re.search(r"[*?\[\]]", name) and not (package_member and name == "[Content_Types].xml"):
        raise PolicyError(f"wildcard path is not explicit authorization: {name!r}")
    return PurePosixPath(name)


def check_policy_path(name, *, allow_pdf=False, package_member=False):
    path = safe_path(name, package_member=package_member)
    parts = {part.lower() for part in path.parts}
    suffix = path.suffix.lower()
    if allow_pdf and name == "article/main.pdf":
        return path
    if (parts & PRIVATE_PARTS or str(path).lower() in PRIVATE_PATHS or path.name.lower() in PRIVATE_FILENAMES or
            suffix in FORBIDDEN_SUFFIXES or path.name == ".DS_Store"):
        raise PolicyError(f"forbidden private/editorial path: {name}")
    if suffix == ".pdf":
        raise PolicyError(f"PDF requires explicit optional entry and --include-paper-pdf: {name}")
    if suffix in OPAQUE_ARCHIVE_SUFFIXES:
        raise PolicyError(f"opaque archive is forbidden: {name}")
    return path


def local_file(root, name):
    path = root
    for component in safe_path(name).parts:
        path = path / component
        if path.is_symlink():
            raise PolicyError(f"symlink is forbidden: {name}")
    if not path.is_file():
        raise PolicyError(f"allowlisted file is missing or not regular: {name}")
    return path


def check_bytes(name, data, *, allow_pdf=False, allow_archive=False,
                expected_members=None, depth=0, budget=None, package_member=False):
    path = check_policy_path(name, allow_pdf=allow_pdf, package_member=package_member)
    if PERSONAL_PATH.search(data):
        raise PolicyError(f"personal filesystem path in public file: {name}")
    if MANUSCRIPT_CONTENT.search(data):
        raise PolicyError(f"editable manuscript content under renamed path: {name}")
    pdf_header = data.lstrip().startswith(b"%PDF-")
    if pdf_header and not (allow_pdf and name == "article/main.pdf"):
        raise PolicyError(f"renamed PDF lacks optional paper authorization: {name}")
    if path.suffix.lower() == ".pdf" and not pdf_header:
        raise PolicyError(f"optional paper PDF lacks a PDF header: {name}")
    is_zip = zipfile.is_zipfile(io.BytesIO(data))
    if path.suffix.lower() in {".zip", ".xlsx"} or is_zip:
        if not allow_archive:
            raise PolicyError(f"archive requires explicit reviewed data-archive authorization: {name}")
        if not is_zip:
            raise PolicyError(f"invalid ZIP archive: {name}")
        if depth and name not in {"data/raw/online_retail.zip", "Online Retail.xlsx"}:
            raise PolicyError(f"forbidden nested archive without specific data exception: {name}")
        if depth >= MAX_ARCHIVE_DEPTH:
            raise PolicyError(f"archive nesting limit exceeded: {name}")
        budget = budget if budget is not None else {"bytes": 0, "entries": 0}
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            names = []
            for info in infos:
                entry = info.filename[:-1] if info.is_dir() else info.filename
                safe_path(entry, package_member=path.suffix.lower() == ".xlsx")
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise PolicyError(f"archive symlink: {name}!{entry}")
                if info.flag_bits & 1:
                    raise PolicyError(f"encrypted archive member: {name}!{entry}")
                if entry in names:
                    raise PolicyError(f"duplicate archive member: {name}!{entry}")
                names.append(entry)
                budget["entries"] += 1
                budget["bytes"] += info.file_size
                if budget["entries"] > MAX_ARCHIVE_ENTRIES or budget["bytes"] > MAX_EXPANDED_BYTES:
                    raise PolicyError(f"archive expansion limit exceeded: {name}")
            files = [info.filename for info in infos if not info.is_dir()]
            if any(entry.startswith(("word/", "ppt/")) for entry in files):
                raise PolicyError(f"forbidden editable Office package: {name}")
            if expected_members is not None and set(files) != set(expected_members):
                raise PolicyError(f"archive members differ from explicit list: {name}")
            spreadsheet = path.suffix.lower() == ".xlsx"
            if spreadsheet and not any(entry.startswith("xl/") for entry in files):
                raise PolicyError(f"invalid XLSX package: {name}")
            for info in infos:
                if info.is_dir():
                    check_policy_path(info.filename[:-1], package_member=spreadsheet)
                    continue
                if spreadsheet and not (info.filename == "[Content_Types].xml" or
                                        info.filename.startswith(("xl/", "_rels/", "docProps/"))):
                    raise PolicyError(f"forbidden XLSX member: {name}!{info.filename}")
                if spreadsheet and not (PurePosixPath(info.filename).suffix.lower() in {".xml", ".rels"} or
                                        info.filename == "_rels/.rels"):
                    raise PolicyError(f"forbidden XLSX member: {name}!{info.filename}")
                check_bytes(info.filename, archive.read(info), allow_archive=True,
                            allow_pdf=allow_pdf and info.filename == "article/main.pdf",
                            depth=depth + 1, budget=budget, package_member=spreadsheet)


def _source_identity(name):
    path = check_policy_path(name)
    if not name.startswith(("experiments/src/", "experiments/scripts/", "experiments/docs/")):
        if not (name.startswith("experiments/data/") and path.name == "SHA256SUMS"):
            raise PolicyError(f"forbidden non-computational snapshot identity: {name}")
    elif path.suffix.lower() not in {".jl", ".py", ".sh", ".md"}:
        raise PolicyError(f"forbidden snapshot source type: {name}")


def load_manifest(root, manifest, *, include_paper_pdf=False):
    manifest_path = Path(manifest)
    if not manifest_path.is_absolute():
        manifest_path = local_file(root, str(manifest_path))
    document = json.loads(manifest_path.read_text())
    if document.get("schema") != 1 or not isinstance(document.get("files"), list):
        raise PolicyError("allowlist must have schema 1 and an explicit files list")
    names = list(document["files"])
    optional = document.get("optional_pdf", [])
    if not isinstance(optional, list) or any(name != "article/main.pdf" for name in optional):
        raise PolicyError("optional_pdf may name only article/main.pdf")
    if len(set(names)) != len(names) or len(set(optional)) != len(optional):
        raise PolicyError("duplicate allowlist path")
    if set(names) & set(optional):
        raise PolicyError("PDF belongs only in optional_pdf, never default files")
    if include_paper_pdf:
        names += optional
    archives = document.get("data_archives", {})
    if not isinstance(archives, dict):
        raise PolicyError("data_archives must map explicit paths to member lists")
    for name, members in archives.items():
        safe_path(name)
        if name not in names or not isinstance(members, list) or not members or len(set(members)) != len(members):
            raise PolicyError(f"data archive needs explicit unique members and a files entry: {name}")
        for member in members:
            check_policy_path(member)
    sources_by_manifest = {}
    payloads = {}
    for name in names:
        check_policy_path(name, allow_pdf=include_paper_pdf)
        payload = local_file(root, name).read_bytes()
        check_bytes(name, payload, allow_pdf=include_paper_pdf,
                    allow_archive=name in archives, expected_members=archives.get(name))
        for prefix, frozen_path in SNAPSHOT_OBJECTS.items():
            if not name.startswith(prefix):
                continue
            if frozen_path not in sources_by_manifest:
                if frozen_path not in names:
                    raise PolicyError("snapshot object requires allowlisted provenance manifest")
                sources = json.loads(local_file(root, frozen_path).read_text()).get("sources", {})
                if not isinstance(sources, dict):
                    raise PolicyError("snapshot sources must be a path-to-hash mapping")
                for original, digest in sources.items():
                    _source_identity(original)
                    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                        raise PolicyError(f"invalid source hash: {original}")
                sources_by_manifest[frozen_path] = sources
            sources = sources_by_manifest[frozen_path]
            digest = PurePosixPath(name).name
            if name != prefix + digest or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise PolicyError(f"invalid content-addressed object path: {name}")
            if digest not in sources.values():
                raise PolicyError(f"unmapped content-addressed object: {name}")
            if hashlib.sha256(payload).hexdigest() != digest:
                raise PolicyError(f"snapshot object hash mismatch: {name}")
        if name == RELEASE_MANIFEST:
            raise PolicyError("generated release manifest cannot be a source allowlist entry")
        payloads[name] = payload
    return document, payloads


def check_archive(path, *, include_paper_pdf=False):
    """Recursively inspect a ZIP, including ZIP/XLSX members, without extraction."""
    path = Path(path)
    check_bytes(path.name, path.read_bytes(), allow_archive=True, allow_pdf=include_paper_pdf)
    return True


def check_git_history(root, *, include_paper_pdf=False, details=None):
    """Inspect every commit reachable from every local ref, plus detached HEAD."""
    root = Path(root)
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)
    refs = git("for-each-ref", "--format=%(refname)").decode().splitlines()
    direct_trees = set()
    for ref in refs:
        peeled = git("rev-parse", "--verify", ref + "^{}").decode().strip()
        kind = git("cat-file", "-t", peeled).decode().strip()
        if kind == "tree":
            direct_trees.add(peeled)
        elif kind != "commit":
            raise PolicyError(f"non-commit Git ref with unnamed payload cannot be certified: {ref}")
    commits = git("rev-list", "--all", "HEAD").decode().splitlines()
    seen = set()
    paths = 0
    for commit in commits + sorted(direct_trees):
        records = git("ls-tree", "-rz", commit).split(b"\0")
        objects = {}
        for record in records:
            if record:
                metadata, raw_name = record.split(b"\t", 1)
                objects[raw_name.decode("utf-8", errors="strict")] = metadata.decode().split()[2]
        snapshot_sources = {}
        for record in records:
            if not record:
                continue
            metadata, raw_name = record.split(b"\t", 1)
            mode, kind, object_id = metadata.decode().split()
            name = raw_name.decode("utf-8", errors="strict")
            check_policy_path(name, allow_pdf=include_paper_pdf)
            paths += 1
            if mode == "120000":
                raise PolicyError(f"Git symlink is forbidden at {commit}:{name}")
            if kind != "blob":
                raise PolicyError(f"uninspectable Git object/submodule: {commit}:{name}")
            for prefix, manifest in SNAPSHOT_OBJECTS.items():
                if not name.startswith(prefix):
                    continue
                if manifest not in snapshot_sources:
                    frozen = objects.get(manifest)
                    if not frozen:
                        raise PolicyError(f"unmapped Git snapshot object: {commit}:{name}")
                    sources = json.loads(git("cat-file", "blob", frozen)).get("sources", {})
                    if not isinstance(sources, dict):
                        raise PolicyError("snapshot sources must be a path-to-hash mapping")
                    for original, digest in sources.items():
                        _source_identity(original)
                        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                            raise PolicyError(f"invalid source hash: {original}")
                    snapshot_sources[manifest] = sources
                digest = PurePosixPath(name).name
                if name != prefix + digest or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise PolicyError(f"invalid Git content-addressed object path: {commit}:{name}")
                if digest not in snapshot_sources[manifest].values():
                    raise PolicyError(f"unmapped Git snapshot object: {commit}:{name}")
                if hashlib.sha256(git("cat-file", "blob", object_id)).hexdigest() != digest:
                    raise PolicyError(f"Git snapshot object hash mismatch: {commit}:{name}")
            key = (name, object_id)
            if key in seen:
                continue
            seen.add(key)
            check_bytes(name, git("cat-file", "blob", object_id), allow_archive=True,
                        allow_pdf=include_paper_pdf)
    if details is not None:
        details.update({"refs": refs, "commits_checked": len(commits),
                        "direct_tree_refs_checked": len(direct_trees),
                        "tree_paths_checked": paths, "distinct_blobs_checked": len(seen)})
    return len(commits)


def validate(root, manifest, *, include_paper_pdf=False, check_history=False, archive=None):
    root = Path(root).resolve()
    document, payloads = load_manifest(root, manifest, include_paper_pdf=include_paper_pdf)
    history = None
    if check_history:
        history = {}
        check_git_history(root, include_paper_pdf=include_paper_pdf, details=history)
    if archive:
        check_archive(archive, include_paper_pdf=include_paper_pdf)
        with zipfile.ZipFile(archive) as package:
            expected = set(payloads) | {RELEASE_MANIFEST}
            if set(package.namelist()) != expected:
                raise PolicyError("archive paths do not match explicit allowlist plus release manifest")
            generated = json.loads(package.read(RELEASE_MANIFEST))
            expected_pdf = include_paper_pdf and bool(document.get("optional_pdf"))
            if (generated.get("schema") != 1 or
                    generated.get("paper_pdf_included") is not expected_pdf or
                    generated.get("editable_manuscript_sources_included") is not False):
                raise PolicyError("release metadata contradicts schema or PDF/manuscript policy")
            entries = generated.get("files", [])
            if {entry.get("path") for entry in entries} != set(payloads) or len(entries) != len(payloads):
                raise PolicyError("release manifest files differ from explicit allowlist")
            for entry in entries:
                name = entry["path"]
                payload = package.read(name)
                if payload != payloads[name] or entry.get("sha256") != hashlib.sha256(payload).hexdigest() or entry.get("bytes") != len(payload):
                    raise PolicyError(f"archive/manifest/local integrity mismatch: {name}")
    return {"valid": True, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "files": len(payloads), "paper_pdf_included": include_paper_pdf and bool(document.get("optional_pdf")),
            "editable_manuscript_sources_included": False, "git_history": history,
            "archive": str(archive) if archive else None,
            "scope": "Local files and locally reachable refs only; no remote/caches/downloads claim."}


def common_arguments(parser):
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--include-paper-pdf", action="store_true",
                        help="Use only after explicit author authorization; enables optional_pdf entries")
    parser.add_argument("--report", type=Path)


def protect_destinations(root, manifest, *, report=None, output=None, archive=None):
    """Reject accidental overwrites and caller-controlled destination symlinks."""
    root = Path(root).absolute()
    manifest_path = Path(manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    document = json.loads(manifest_path.read_text())
    names = document.get("files", []) + document.get("optional_pdf", [])
    protected = {manifest_path.resolve()}
    for name in names:
        protected.add((root / safe_path(name)).resolve())
    if archive:
        protected.add(Path(archive).resolve())
    for destination, label in ((output, "output"), (report, "report")):
        if destination is None:
            continue
        destination = Path(destination).absolute()
        if destination.is_symlink():
            raise PolicyError(f"{label} symlink is forbidden: {destination}")
        try:
            relative = destination.relative_to(root)
        except ValueError:
            relative = None
        if relative is not None:
            cursor = root
            for component in relative.parts:
                cursor /= component
                if cursor.is_symlink():
                    raise PolicyError(f"{label} symlink parent is forbidden: {destination}")
        aliases_input = destination.resolve() in protected
        if destination.exists() and not aliases_input:
            aliases_input = any(source.exists() and destination.samefile(source) for source in protected)
        if aliases_input:
            raise PolicyError(f"{label} cannot replace an input, manifest or archive: {destination}")
        if label == "output":
            if destination.suffix.lower() != ".zip":
                raise PolicyError("output must have a .zip extension")
            protected.add(destination.resolve())


def write_report(path, report):
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    common_arguments(parser)
    parser.add_argument("--check-git-history", action="store_true")
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    safe_report = None
    try:
        protect_destinations(args.root, args.manifest, report=args.report, archive=args.archive)
        safe_report = args.report
        report = validate(args.root, args.manifest, include_paper_pdf=args.include_paper_pdf,
                          check_history=args.check_git_history, archive=args.archive)
    except (PolicyError, OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        report = {"valid": False, "error": str(error)}
        write_report(safe_report, report)
        print("Publication policy rejected: " + str(error), file=sys.stderr)
        return 1
    write_report(safe_report, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
