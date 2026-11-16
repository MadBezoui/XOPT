#!/usr/bin/env python3
"""Materialize a reviewed public-only snapshot, preserving the original local provenance.

This prepares local files only. It never changes Git refs or uploads anything.
The historical provenance manifest is projected to omit private source objects;
all historical records and every source hash they actually cite remain unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from validate_publication import PolicyError, check_policy_path, local_file, safe_path, validate

FROZEN = "experiments/provenance/frozen_manifest.json"
OBJECTS = "experiments/provenance/objects/"


def materialize(root, manifest, output):
    root = Path(root).resolve()
    output = Path(output).absolute()
    if output.is_symlink() or output.exists():
        raise PolicyError("snapshot output must be a new path")
    output_parent = output.parent.resolve(strict=True)
    output = output_parent / output.name
    if output == root or root in output.parents:
        raise PolicyError("snapshot output must be outside the working project")
    manifest_rel = safe_path(str(manifest))
    manifest_data = local_file(root, str(manifest_rel)).read_bytes()
    document = json.loads(manifest_data)
    names = document.get("files", [])
    if document.get("schema") != 1 or not isinstance(names, list) or len(set(names)) != len(names):
        raise PolicyError("snapshot requires an explicit schema-1 allowlist with unique paths")
    for name in names:
        check_policy_path(name)
    if FROZEN not in names:
        raise PolicyError("snapshot requires a frozen provenance manifest")
    original = local_file(root, FROZEN).read_bytes()
    frozen = json.loads(original)
    sources = frozen.get("sources")
    records = frozen.get("historical_records")
    if not isinstance(sources, dict) or not isinstance(records, dict):
        raise PolicyError("invalid frozen provenance")
    projected = {}
    for name, digest in sources.items():
        try:
            check_policy_path(name)
        except PolicyError:
            continue
        if OBJECTS + digest not in names:
            raise PolicyError("allowlist omits a retained historical source object: " + name)
        projected[name] = digest
    removed = set(sources) - set(projected)
    if any(OBJECTS + sources[name] in names for name in removed):
        raise PolicyError("private frozen source object remains in the allowlist")
    for name, entry in records.items():
        if name not in names:
            raise PolicyError("historical record missing from allowlist: " + name)
        data = local_file(root, name).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise PolicyError("historical record fingerprint changed: " + name)
        for line in data.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cited = row.get("source_sha256", {})
            cited = cited if isinstance(cited, dict) else {"experiments/src/XOPT.jl": cited}
            for source, digest in cited.items():
                source = source if "/" in source else "experiments/src/" + source
                if projected.get(source) != digest:
                    raise PolicyError("historical record cites missing projected source: " + source)
    frozen["sources"] = projected
    frozen["projection"] = {
        "original_frozen_manifest_sha256": hashlib.sha256(original).hexdigest(),
        "omitted_private_source_count": len(removed),
        "scope": "Public projection; the unmodified complete retrospective manifest stays local. Historical records and their cited source identities are unchanged.",
    }
    temp = Path(tempfile.mkdtemp(prefix=".xopt-public-snapshot-", dir=output_parent))
    try:
        for name in names:
            dest = temp.joinpath(*safe_path(name).parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if name == FROZEN:
                dest.write_text(json.dumps(frozen, indent=2) + "\n")
            else:
                shutil.copyfile(local_file(root, name), dest)
        staged_manifest = temp.joinpath(*manifest_rel.parts)
        if str(manifest_rel) not in names:
            staged_manifest.parent.mkdir(parents=True, exist_ok=True)
            staged_manifest.write_bytes(manifest_data)
        validate(temp, str(manifest_rel))
        os.rename(temp, output)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    return {"snapshot": str(output), "files": len(names), "omitted_private_sources": len(removed),
            "original_frozen_manifest_sha256": hashlib.sha256(original).hexdigest(), "published": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", default="experiments/docs/publication_allowlist.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = materialize(args.root, args.manifest, args.output)
    except (PolicyError, ValueError, KeyError, OSError) as exc:
        print("Public snapshot rejected: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
