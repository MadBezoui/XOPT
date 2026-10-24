"""Publication boundaries, exercised through real files, ZIPs and Git repositories."""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def zipped(files):
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return result.getvalue()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.put("experiments/src/model.jl", "module Model\nend\n")
        self.put("article/main.tex", "\\documentclass{article}\n")
        self.put("article/main.pdf", b"%PDF-1.4\nexample\n")
        self.manifest = {
            "schema": 1,
            "files": ["experiments/src/model.jl"],
            "optional_pdf": ["article/main.pdf"],
            "data_archives": {},
        }
        self.save_manifest()

    def put(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data, str) else data)
        return path

    def save_manifest(self):
        self.put("allowlist.json", json.dumps(self.manifest))

    def run_script(self, script, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), "--root", str(self.root),
             "--manifest", "allowlist.json", *map(str, arguments)],
            text=True, capture_output=True,
        )

    def validate(self, *args):
        self.save_manifest()
        return self.run_script("validate_publication.py", *args)

    def assert_rejected(self, result, reason):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(reason, result.stderr + result.stdout)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_git(self):
        self.git("init", "-q")
        self.git("config", "user.name", "Publication regression")
        self.git("config", "user.email", "regression@example.invalid")
        self.git("add", "experiments/src/model.jl")
        self.git("commit", "-qm", "Clean computational source")

    def test_build_includes_only_explicit_files_and_reproducible_integrity_manifest(self):
        self.put("experiments/results/unreviewed.json", "{}")
        result = self.run_script("build_release.py", "--output", self.root / "release.zip")
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.root / "release.zip") as archive:
            self.assertEqual(set(archive.namelist()), {
                "experiments/src/model.jl", "experiments/release_manifest.json"})
            metadata = json.loads(archive.read("experiments/release_manifest.json"))
            self.assertEqual(metadata["files"][0]["path"], "experiments/src/model.jl")
            self.assertEqual(metadata["files"][0]["sha256"],
                             hashlib.sha256(b"module Model\nend\n").hexdigest())
        second = self.run_script("build_release.py", "--output", self.root / "second.zip")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((self.root / "release.zip").read_bytes(),
                         (self.root / "second.zip").read_bytes())

    def test_pdf_needs_opt_in_and_explicit_manifest_entry(self):
        result = self.run_script("build_release.py", "--output", self.root / "release.zip",
                                 "--include-paper-pdf")
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.root / "release.zip") as archive:
            self.assertIn("article/main.pdf", archive.namelist())
        self.manifest["files"].append("article/main.pdf")
        self.assert_rejected(self.validate(), "PDF")

    def test_forbidden_manuscript_source_even_if_explicitly_listed(self):
        for name in ("article/main.tex", "references.BIB", "template.cls", "template.dotx", "paper.docx",
                     "experiments/tables/table.csv", "figure.svg"):
            with self.subTest(name=name):
                self.put(name, "private editable manuscript")
                self.manifest["files"] = [name]
                self.assert_rejected(self.validate(), "forbidden")

    def test_renamed_document_source_is_rejected_by_content(self):
        for content in ("\\documentclass{article}\n\\begin{document}",
                        "\\begin{tabular}{ll}\nprivate & paper\n\\end{tabular}",
                        "<svg xmlns='http://www.w3.org/2000/svg'>private figure</svg>"):
            with self.subTest(content=content):
                self.put("experiments/src/notebook.txt", content)
                self.manifest["files"] = ["experiments/src/notebook.txt"]
                self.assert_rejected(self.validate(), "manuscript content")

    def test_manifest_rejects_absolute_traversal_glob_and_duplicate_paths(self):
        for name in ("/tmp/private.py", "../private.py", "experiments/../private.py",
                     "C:/private.py", "experiments\\secret.py", "experiments/src/*.jl"):
            with self.subTest(name=name):
                self.manifest["files"] = [name]
                self.assert_rejected(self.validate(), "path")
        self.manifest["files"] = ["experiments/src/model.jl"] * 2
        self.assert_rejected(self.validate(), "duplicate")

    def test_symlink_and_symlinked_parent_are_rejected(self):
        (self.root / "experiments/src/link.jl").symlink_to("model.jl")
        self.manifest["files"] = ["experiments/src/link.jl"]
        self.assert_rejected(self.validate(), "symlink")
        (self.root / "shortcut").symlink_to("experiments/src", target_is_directory=True)
        self.manifest["files"] = ["shortcut/model.jl"]
        self.assert_rejected(self.validate(), "symlink")

    def test_unlisted_archive_and_nested_manuscript_are_rejected(self):
        self.put("experiments/results/backup.zip", zipped({"main.tex": "secret"}))
        self.manifest["files"] = ["experiments/results/backup.zip"]
        self.assert_rejected(self.validate(), "archive")
        self.put("data/raw/online_retail.zip", zipped({
            "Online Retail.xlsx": zipped({"xl/hidden.tex": "secret"})}))
        self.manifest["files"] = ["data/raw/online_retail.zip"]
        self.manifest["data_archives"] = {"data/raw/online_retail.zip": ["Online Retail.xlsx"]}
        self.assert_rejected(self.validate(), "forbidden")

    def test_unreviewed_nested_archive_is_rejected_even_with_safe_contents(self):
        self.put("data/raw/outer.zip", zipped({"inner.zip": zipped({"model.jl": "module M\nend"})}))
        self.manifest["files"] = ["data/raw/outer.zip"]
        self.manifest["data_archives"] = {"data/raw/outer.zip": ["inner.zip"]}
        self.assert_rejected(self.validate(), "forbidden nested archive")

    def test_public_retail_xlsx_archive_is_recursively_validated(self):
        book = zipped({"[Content_Types].xml": "<Types/>", "xl/workbook.xml": "<workbook/>",
                       "_rels/.rels": "<Relationships/>"})
        self.put("data/raw/online_retail.zip", zipped({"Online Retail.xlsx": book}))
        self.manifest["files"].append("data/raw/online_retail.zip")
        self.manifest["data_archives"] = {"data/raw/online_retail.zip": ["Online Retail.xlsx"]}
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.put("data/raw/online_retail.zip", zipped({"Online Retail.xlsx": book,
                                                    "extra.txt": "unreviewed"}))
        self.assert_rejected(self.validate(), "members")

    def test_archive_rejects_traversal_symlink_and_duplicate_members(self):
        for kind in ("traversal", "symlink", "duplicate"):
            with self.subTest(kind=kind):
                memory = io.BytesIO()
                with zipfile.ZipFile(memory, "w") as archive:
                    if kind == "traversal":
                        archive.writestr("../Online Retail.xlsx", b"data")
                    elif kind == "symlink":
                        info = zipfile.ZipInfo("Online Retail.xlsx")
                        info.create_system = 3
                        info.external_attr = (stat.S_IFLNK | 0o777) << 16
                        archive.writestr(info, "../../article/main.tex")
                    else:
                        archive.writestr("Online Retail.xlsx", zipped({"xl/workbook.xml": "<w/>"}))
                        import warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", UserWarning)
                            archive.writestr("Online Retail.xlsx", b"second")
                self.put("data/raw/online_retail.zip", memory.getvalue())
                self.manifest["files"] = ["data/raw/online_retail.zip"]
                self.manifest["data_archives"] = {"data/raw/online_retail.zip": ["Online Retail.xlsx"]}
                self.assert_rejected(self.validate(), kind if kind != "traversal" else "path")

    def test_content_addressed_objects_require_safe_original_identity_and_hash(self):
        payload = b"module Historic\nend\n"
        digest = hashlib.sha256(payload).hexdigest()
        name = "experiments/provenance/objects/" + digest
        self.put(name, payload)
        self.manifest["files"] = [name, "experiments/provenance/frozen_manifest.json"]
        frozen = {"sources": {"experiments/src/model.jl": digest}}
        self.put("experiments/provenance/frozen_manifest.json", json.dumps(frozen))
        self.assertEqual(self.validate().returncode, 0)
        self.put(name, b"changed")
        self.assert_rejected(self.validate(), "hash")
        self.put(name, payload)
        self.put("experiments/provenance/frozen_manifest.json",
                 json.dumps({"sources": {"article/main.tex": digest}}))
        self.assert_rejected(self.validate(), "forbidden")
        self.put("experiments/provenance/frozen_manifest.json", json.dumps({"sources": {}}))
        self.assert_rejected(self.validate(), "unmapped")

    def test_git_checks_deleted_manuscript_and_non_head_refs(self):
        self.init_git()
        clean = self.git("rev-parse", "HEAD")
        self.git("add", "article/main.tex")
        self.git("commit", "-qm", "Private source must never become public")
        self.git("tag", "private-snapshot")
        self.git("checkout", "-q", "--detach", clean)
        self.assert_rejected(self.validate("--check-git-history"), "forbidden")

    def test_git_checks_history_after_manuscript_is_deleted(self):
        self.init_git()
        self.git("add", "article/main.tex")
        self.git("commit", "-qm", "Private source")
        self.git("rm", "-q", "article/main.tex")
        self.git("commit", "-qm", "Deletion is insufficient")
        self.assert_rejected(self.validate("--check-git-history"), "forbidden")

    def test_builder_always_checks_git_history_before_writing(self):
        self.init_git()
        self.put("hidden.zip", zipped({"nested.zip": zipped({"paper.tex": "secret"})}))
        self.git("add", "hidden.zip")
        self.git("commit", "-qm", "Nested private payload")
        result = self.run_script("build_release.py", "--output", self.root / "release.zip")
        self.assert_rejected(result, "forbidden")
        self.assertFalse((self.root / "release.zip").exists())

    def test_git_rejects_refs_pointing_outside_commit_history(self):
        self.init_git()
        result = subprocess.run(["git", "-C", str(self.root), "hash-object", "-w", "--stdin"],
                                input=b"private detached blob", capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.git("update-ref", "refs/private/uninspectable", result.stdout.decode().strip())
        self.assert_rejected(self.validate("--check-git-history"), "non-commit")

    def test_git_inspects_tree_refs_without_mutating_them(self):
        self.init_git()
        tree = self.git("write-tree")
        self.git("update-ref", "refs/private/tree-snapshot", tree)
        result = self.validate("--check-git-history")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.git("add", "article/main.tex")
        private_tree = self.git("write-tree")
        self.git("update-ref", "refs/private/tree-snapshot", private_tree)
        self.assert_rejected(self.validate("--check-git-history"), "forbidden")
        self.assertEqual(self.git("rev-parse", "refs/private/tree-snapshot"), private_tree)

    def test_git_snapshot_objects_require_original_identity(self):
        self.init_git()
        payload = b"module Historic\nend\n"
        name = "experiments/provenance/objects/" + hashlib.sha256(payload).hexdigest()
        self.put(name, payload)
        self.git("add", name)
        self.git("commit", "-qm", "Unmapped hidden object")
        self.assert_rejected(self.validate("--check-git-history"), "unmapped")

    def test_renamed_word_package_is_rejected_in_git_history(self):
        self.init_git()
        self.put("payload.bin", zipped({"word/document.xml": "<document>private paper</document>"}))
        self.git("add", "payload.bin")
        self.git("commit", "-qm", "Renamed Word document")
        self.assert_rejected(self.validate("--check-git-history"), "forbidden")

    def test_nested_pdf_does_not_inherit_optional_paper_pdf_authorization(self):
        self.put("data/raw/archive.zip", zipped({"paper.pdf": b"%PDF-1.4"}))
        self.manifest["files"] = ["data/raw/archive.zip"]
        self.manifest["data_archives"] = {"data/raw/archive.zip": ["paper.pdf"]}
        self.assert_rejected(self.validate("--include-paper-pdf"), "PDF")

    def test_pdf_cannot_be_renamed_around_optional_authorization(self):
        self.put("experiments/results/payload.dat", b"%PDF-1.4\nprivate paper\n")
        self.manifest["files"] = ["experiments/results/payload.dat"]
        for options in ((), ("--include-paper-pdf",)):
            with self.subTest(options=options):
                self.assert_rejected(self.validate(*options), "PDF")
        self.manifest["files"] = ["experiments/src/model.jl"]
        self.put("article/main.pdf", "editable prose renamed as a PDF")
        self.assert_rejected(self.validate("--include-paper-pdf"), "PDF")

    def test_transient_and_superseded_results_are_never_distribution_inputs(self):
        for name in ("experiments/results/correction.json.part",
                     "experiments/results/corrections_20261024/superseded/old.json"):
            with self.subTest(name=name):
                self.put(name, "{}")
                self.manifest["files"] = [name]
                self.assert_rejected(self.validate(), "forbidden")

    def test_release_metadata_cannot_misstate_pdf_source_policy_or_schema(self):
        archive = self.root / "release.zip"
        result = self.run_script("build_release.py", "--output", archive)
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(archive) as original:
            files = {name: original.read(name) for name in original.namelist()}
        metadata = json.loads(files["experiments/release_manifest.json"])
        for key, value in (("schema", 999), ("paper_pdf_included", True),
                           ("editable_manuscript_sources_included", True)):
            with self.subTest(key=key):
                altered = dict(metadata, **{key: value})
                archive.write_bytes(zipped(dict(files, **{
                    "experiments/release_manifest.json": json.dumps(altered)})))
                self.assert_rejected(self.validate("--archive", archive), "metadata")

    def test_builder_rejects_symlinked_output_without_touching_target(self):
        original = (self.root / "article/main.tex").read_bytes()
        link = self.root / "release.zip"
        link.symlink_to(self.root / "article/main.tex")
        result = self.run_script("build_release.py", "--output", link)
        self.assert_rejected(result, "symlink")
        self.assertEqual((self.root / "article/main.tex").read_bytes(), original)

    def test_report_cannot_overwrite_inputs_manifest_or_archive(self):
        for report in (self.root / "experiments/src/model.jl", self.root / "allowlist.json",
                       self.root / "release.zip"):
            with self.subTest(report=report):
                result = self.run_script("build_release.py", "--output", self.root / "release.zip",
                                         "--report", report)
                self.assert_rejected(result, "report")
                self.assertEqual((self.root / "experiments/src/model.jl").read_text(), "module Model\nend\n")
                self.assertEqual(json.loads((self.root / "allowlist.json").read_text()), self.manifest)

    def test_hardlinked_report_cannot_truncate_an_input(self):
        source = self.root / "experiments/src/model.jl"
        report = self.root / "report.json"
        os.link(source, report)
        for script, options in (("validate_publication.py", ()),
                                ("build_release.py", ("--output", self.root / "release.zip"))):
            with self.subTest(script=script):
                result = self.run_script(script, *options, "--report", report)
                self.assert_rejected(result, "report")
                self.assertEqual(source.read_text(), "module Model\nend\n")

    def test_failed_build_does_not_replace_existing_output(self):
        self.put("release.zip", b"preserve existing distribution")
        self.manifest["files"].append("article/main.tex")
        self.save_manifest()
        result = self.run_script("build_release.py", "--output", self.root / "release.zip")
        self.assert_rejected(result, "forbidden")
        self.assertEqual((self.root / "release.zip").read_bytes(), b"preserve existing distribution")


if __name__ == "__main__":
    unittest.main()
