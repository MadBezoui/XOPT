"""Verify current sources or explicitly preserved pre-correction source bytes.

Historical source identity is never presented as current-code validation.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_path(root, name):
    root = Path(root).resolve()
    rel = PurePosixPath(name)
    if not name or rel.is_absolute() or ".." in rel.parts or "\\" in name:
        raise ValueError(f"Unsafe artifact path: {name!r}")
    path = root.joinpath(*rel.parts)
    for parent in [path, *path.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Symlink is not a provenance source: {name}")
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Path escapes artifact root: {name}")
    return path


def frozen_manifest(root):
    p = Path(root) / "experiments/provenance/frozen_manifest.json"
    return json.loads(p.read_text()) if p.exists() else {"sources": {}, "historical_records": {}}


def verify_source(root, name, expected, *, current_only=False):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError(f"Invalid source fingerprint for {name}")
    path = checked_path(root, name)
    if path.is_file() and sha256(path) == expected:
        return "current"
    manifest = frozen_manifest(root)
    if not current_only and manifest["sources"].get(name) == expected:
        blob = checked_path(root, "experiments/provenance/objects/" + expected)
        if blob.is_file() and sha256(blob) == expected:
            return "historical"
    raise ValueError(f"Source identity mismatch: {name} ({expected})")


def verify_sources(root, sources, *, current_only=False, required=None):
    if isinstance(sources, str):
        sources = {"experiments/src/XOPT.jl": sources}
    if required is not None and set(sources) != set(required):
        raise ValueError("Incomplete producing-source manifest")
    states = []
    for name, expected in sources.items():
        name = name if "/" in name else "experiments/src/" + name
        states.append(verify_source(root, name, expected, current_only=current_only))
    return states


def verify_frozen_record(root, path):
    path = Path(path).resolve()
    name = path.relative_to(Path(root).resolve()).as_posix()
    entry = frozen_manifest(root)["historical_records"].get(name)
    if entry and sha256(path) != entry["sha256"]:
        raise ValueError(f"Historical records changed: {name}; retain originals and add a separate correction")


def verify_snapshot(root):
    manifest = frozen_manifest(root)
    if not manifest["sources"] or not manifest["historical_records"]:
        raise ValueError("Missing frozen computational provenance manifest")
    for name, digest in manifest["sources"].items():
        checked_path(root, name)
        blob = checked_path(root, "experiments/provenance/objects/" + digest)
        if not blob.is_file() or sha256(blob) != digest:
            raise ValueError(f"Missing or corrupted frozen source: {name}")
    for name, entry in manifest["historical_records"].items():
        path = checked_path(root, name)
        if not path.is_file() or sha256(path) != entry["sha256"]:
            raise ValueError(f"Historical records missing or changed: {name}")
    return manifest
