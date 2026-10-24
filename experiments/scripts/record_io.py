"""Read immutable experiments and apply separately bound numerical corrections."""
import copy
import hashlib
import json
from pathlib import Path
from provenance import checked_path, sha256, verify_frozen_record, verify_sources

CORRECTIONS = "experiments/results/corrections_20261024"
UC_KEY = "tiny_2020-07-06_s1_h15|[(3, 2, 1)]|strong|M"
CORRECTION_SOURCES = {"experiments/src/XOPT.jl", "experiments/src/uc.jl", "experiments/src/robustness.jl",
                      "experiments/scripts/run_corrections.jl", "experiments/scripts/run_robustness.jl",
                      "experiments/docs/correction_protocol_20261024.md"}


def read_records(path, root, *, verify=True):
    path = Path(path)
    if verify:
        verify_frozen_record(root, path)
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if verify:
        for row in rows:
            verify_sources(root, row.get("source_sha256", {}))
    return rows


def apply_uc_correction(rows, root, *, required=True):
    path = checked_path(root, CORRECTIONS + "/uc_correction.json")
    if not path.exists():
        if required:
            raise ValueError("Missing explicit correction for the known UC false optimality result")
        return rows
    correction = json.loads(path.read_text())
    if correction.get("key") != UC_KEY:
        raise ValueError("Unexpected UC correction key")
    source_file = checked_path(root, correction["original_file"])
    if sha256(source_file) != correction["original_file_sha256"]:
        raise ValueError("UC correction refers to changed historical input")
    lines = [line for line in source_file.read_text().splitlines() if json.loads(line)["key"] == UC_KEY]
    if len(lines) != 1 or hashlib.sha256(lines[0].encode()).hexdigest() != correction["original_record_sha256"]:
        raise ValueError("UC correction historical record identity mismatch")
    verify_sources(root, correction["source_sha256"], current_only=True, required=CORRECTION_SOURCES)
    if correction.get("verification", {}).get("valid") is not True:
        raise ValueError("UC correction has no successful fresh witness verification")
    replacement = correction["result"]
    if replacement.get("status") != "SOLVER_VALIDATED":
        raise ValueError("UC correction is unresolved")
    result = copy.deepcopy(rows)
    matches = [a for a in result if a["key"] == UC_KEY]
    if len(matches) != 1:
        raise ValueError("UC correction target is missing or duplicated")
    row = matches[0]
    if abs(replacement["objective"] - row["enumeration"]["objective"]) > 1e-6:
        raise ValueError("UC correction still disagrees with independent enumeration")
    row["historical_dual"] = row["dual"]
    row["dual"] = replacement
    row["dual_verification"] = correction["verification"]
    row["correction"] = {"file": str(path.relative_to(root)), "recorded_utc": correction["recorded_utc"]}
    row["status"] = "/".join(row[k]["status"] for k in ("enumeration", "dual", "trajectory"))
    return result


def current_radii(root):
    path = checked_path(root, CORRECTIONS + "/robustness_revalidated.jsonl")
    if not path.is_file():
        raise ValueError("Missing current radius records with complete algorithm/input provenance")
    rows = read_records(path, root)
    original = checked_path(root, "experiments/results/main.jsonl")
    selected = {}
    for line in original.read_text().splitlines():
        record = json.loads(line)
        if record["job"]["method"] == "ccg" and record["status"] == "SOLVER_VALIDATED":
            selected[record["key"]] = hashlib.sha256(line.encode()).hexdigest()
    for row in rows:
        verify_sources(root, row["source_sha256"], current_only=True, required=CORRECTION_SOURCES)
        if row["input_file"] != "experiments/results/main.jsonl" or selected.get(row["key"]) != row["input_record_sha256"]:
            raise ValueError("Radius individual input record identity mismatch")
        if row["options"] != {"rho_max": .25, "atol": 1e-5, "time_limit": 60.}:
            raise ValueError("Radius options differ from the declared correction protocol")
        input_file = checked_path(root, row["input_file"])
        if sha256(input_file) != row["input_sha256"]:
            raise ValueError("Radius input identity mismatch")
    return rows
