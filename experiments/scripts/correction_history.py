"""Verify preserved pre-revision correction records and their exact source bytes."""
import json
import re
from pathlib import Path

from provenance import checked_path, sha256


def verify_correction_history(root):
    root = Path(root).resolve()
    base = "experiments/provenance/corrections_20261024"
    manifest = json.loads(checked_path(root, base + "/manifest.json").read_text())
    sources, records = manifest["sources"], manifest["records"]
    if not sources or not records:
        raise ValueError("Incomplete preserved correction evidence")
    expected = {"experiments/results/corrections_20261024/" + name for name in
                ("uc_correction.json", "robustness_revalidated.jsonl", "current_validation.json")}
    if set(records) != expected:
        raise ValueError("Incomplete historical correction record set")
    for name, digest in sources.items():
        checked_path(root, name)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid correction source digest: {name}")
        stored = checked_path(root, base + "/objects/" + digest)
        if not stored.is_file() or sha256(stored) != digest:
            raise ValueError(f"Missing or altered correction source bytes: {name}")
    for name, digest in records.items():
        record = checked_path(root, name)
        if not record.is_file() or sha256(record) != digest:
            raise ValueError(f"Missing or altered historical correction: {name}")
        lines = record.read_text().splitlines()
        if not lines:
            raise ValueError(f"Empty historical correction: {name}")
        for line in lines:
            for source, expected_digest in json.loads(line)["source_sha256"].items():
                if sources.get(source) != expected_digest:
                    raise ValueError(f"Historical correction source binding mismatch: {source}")
    return {"sources_verified": len(sources), "records_verified": len(records),
            "scope": "Retrospectively preserved bytes; not an execution-time provenance claim"}
