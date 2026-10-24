"""Final gate for every study, immutable attempts and explicit current corrections.

Importing this module has no side effects. Historical source checks and fresh
current-code numerical checks are reported separately, never conflated.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from provenance import checked_path, sha256, verify_snapshot, verify_source, verify_sources
from record_io import CORRECTIONS, apply_uc_correction, current_radii, read_records

PRIMARY = {"correctness": 40, "main": 120, "sensitivity": 72, "scale": 36,
           "capacity": 16, "long": 12, "multifoil": 24}
STUDIES = {"audit_long": 48, "audit_sparsity": 600, "audit_margin": 180,
           "audit_naive": 288, "audit_bound": 100, "levers_enum": 40,
           "levers_bench": 210, "uc_enum": 140, "uc_bench": 160}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_success(result, verification, context):
    require(result.get("status") in ("SOLVER_VALIDATED", "FEASIBLE_VALIDATED"), f"Unexpected success status: {context}")
    require(verification is not None and verification.get("valid") is True, f"Failed/missing witness validation: {context}")
    require(finite(result.get("objective")), f"Nonfinite intervention objective: {context}")
    lower = result.get("lower_bound")
    require(lower is None or (finite(lower) and lower <= result["objective"] + 1e-5), f"Contradictory bounds: {context}")
    for name in ("y", "u"):
        if name in result:
            def flat(values):
                for value in values:
                    if isinstance(value, list):
                        yield from flat(value)
                    else:
                        yield value
            values = list(flat(result[name]))
            require(values and all(finite(x) and -1e-8 <= x <= 1+1e-8 and abs(x-round(x)) <= 1e-8 for x in values),
                    f"Nonbinary witness: {context}")


def validate_enum_cases(rows, label, expected):
    require(len(rows) == expected, f"{label}: expected {expected} cases, found {len(rows)}")
    require(len({r["key"] for r in rows}) == expected, f"Duplicate {label} case")
    feasible = 0
    for row in rows:
        enum = row["enumeration"]
        require(enum["status"] in ("OPTIMAL", "INFEASIBLE"), f"Unresolved reference enumeration: {label}/{row['key']}")
        for method in ("dual", "trajectory"):
            result = row[method]
            context = f"{label}/{row['key']}/{method}"
            if enum["status"] == "INFEASIBLE":
                require(result["status"] == "SOLVER_INFEASIBLE", f"Enumeration status disagreement: {context}")
            else:
                validate_success(result, row.get(method+"_verification"), context)
                require(abs(result["objective"] - enum["objective"]) <= 1e-6, f"Enumeration objective disagreement: {context}")
        feasible += enum["status"] == "OPTIMAL"
    return {"cases": len(rows), "feasible": feasible, "all_methods_agree": True}


def validate_anytime(output, context):
    upper, lower = output.get("upper_bound"), output.get("lower_bound")
    if upper is not None:
        require(finite(upper) and finite(lower) and lower <= upper+1e-5, f"Invalid anytime bounds: {context}")
        validate_success(output["result"], output.get("verification"), context)
        require(abs(output["result"]["objective"]-upper) <= 1e-5, f"Anytime objective mismatch: {context}")
        require(abs(output["absolute_gap"]-max(0, upper-lower)) <= 1e-5, f"Anytime gap mismatch: {context}")
    if output.get("status") == "SOLVER_VALIDATED":
        require(upper is not None and upper-lower <= 1e-5, f"Unclosed optimality gap: {context}")
    if output.get("status") == "SOLVER_INFEASIBLE":
        require(upper is None, f"Infeasible status with incumbent: {context}")


def load_all(root):
    manifest = verify_snapshot(root)
    files = {}
    for name, entry in manifest["historical_records"].items():
        rows = read_records(root/name, root)
        require(len(rows) == entry["records"], f"Historical count mismatch: {name}")
        identity = [(r.get("profile"), r["key"], r.get("method")) for r in rows]
        require(len(set(identity)) == len(rows), f"Duplicate record identity: {name}")
        files[Path(name).name] = rows
    return files


def study(files, prefix, expected):
    rows = [r for filename, records in sorted(files.items()) if filename.startswith(prefix+"_w") for r in records]
    require(len(rows) == expected and len({r["key"] for r in rows}) == expected, f"Missing/duplicate {prefix}: {len(rows)}/{expected}")
    return rows


def validation_id(filename, row, variant):
    profile = row["profile"]+"|" if filename == "external_reference.jsonl" else ""
    return filename+"|"+profile+row["key"]+"|"+variant


def expected_validation_ids(files):
    expected = {}
    for filename, rows in files.items():
        for row in rows:
            variants = []
            if filename in {p+".jsonl" for p in PRIMARY}:
                if row["status"] == "SOLVER_VALIDATED":
                    variants = [("menu" if filename == "capacity.jsonl" else "result", True)]
            elif filename == "external_reference.jsonl":
                if row["result"]["status"] == "SOLVER_VALIDATED":
                    variants = [(row["method"], True)]
            elif filename.startswith("revision_"):
                if row.get("output", {}).get("upper_bound") is not None:
                    variants = [("result", True)]
            elif filename.startswith(("audit_long_w", "audit_sparsity_w")):
                if row["output"].get("upper_bound") is not None:
                    variants = [("result", True)]
            elif filename.startswith("audit_margin_w"):
                if row["result"]["status"] == "SOLVER_VALIDATED":
                    variants = [("result", True)]
            elif filename.startswith("audit_naive_w"):
                variants = [(k, row[k+"_verification"]["valid"]) for k in ("correct", "naive") if row[k]["status"] == "SOLVER_VALIDATED"]
            elif filename.startswith(("levers_enum_w", "uc_enum_w")):
                variants = [(k, True) for k in ("dual", "trajectory") if row[k]["status"] == "SOLVER_VALIDATED"]
            elif filename.startswith(("levers_bench_w", "uc_bench_w")):
                if row["result"]["status"] == "SOLVER_VALIDATED":
                    variants = [("result", True)]
            for variant, valid in variants:
                expected[validation_id(filename, row, variant)] = valid
    return expected


def validate_current_report(root, files):
    path = root/CORRECTIONS/"current_validation.json"
    require(path.is_file(), "Run validate_updates.jl to produce current-code numerical validations")
    current = json.loads(path.read_text())
    verify_sources(root, current["source_sha256"], current_only=True,
                   required={"experiments/src/XOPT.jl", "experiments/src/levers.jl", "experiments/src/uc.jl",
                             "experiments/scripts/validate_updates.jl", "experiments/docs/correction_protocol_20261024.md"})
    inputs = {"experiments/results/"+name: sha256(root/"experiments/results"/name) for name in files}
    for name in ("uc_correction.json", "robustness_revalidated.jsonl"):
        inputs[CORRECTIONS+"/"+name] = sha256(root/CORRECTIONS/name)
    require(current["input_sha256"] == inputs, "Current witness validation does not bind all current input files")
    expected = expected_validation_ids(files)
    checks = current["checks"]
    require(len(checks) == len(expected) and {r["id"] for r in checks} == set(expected), "Incomplete/duplicate fresh witness checks")
    for item in checks:
        residual = item.get("objective_residual")
        require(isinstance(item.get("verification", {}).get("valid"), bool) and isinstance(item.get("binary"), bool)
                and finite(residual) and residual >= 0, f"Incomplete fresh check evidence: {item['id']}")
        computed = item["verification"]["valid"] and item["binary"] and residual <= 1e-5
        require(item["valid"] is computed, f"Contradictory fresh check evidence: {item['id']}")
        require(item["expected_valid"] is expected[item["id"]], f"Changed expected result: {item['id']}")
        require(item["valid"] is expected[item["id"]] and item["passed"] is True, f"Fresh witness check failed: {item['id']}")
    require(current["all_passed"] is True, "Current-code witness validation did not pass")
    return {"checks": len(checks), "intentionally_invalid_controls": sum(not v for v in expected.values()), "current_code": True}


def validate(root):
    root = Path(root).resolve()
    names = {p.name for p in root.iterdir() if not p.name.startswith('.')}
    require({"data", "experiments"} <= names <= {"article", "data", "experiments", "README.md", "README.en.md", "CITATION.cff"},
            f"Unexpected root content: {sorted(names)}")
    downloads = json.loads((root/"data/metadata/downloads.json").read_text())
    for item in downloads:
        path = checked_path(root, item["file"])
        require(path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"], f"Raw input changed: {item['file']}")
    pglib = root/"experiments/data/pglib_uc"
    for line in (pglib/"SHA256SUMS").read_text().splitlines():
        digest, name = line.split()
        require(sha256(checked_path(root, "experiments/data/pglib_uc/"+name.lstrip('*'))) == digest, f"PGLib input changed: {name}")
    files = load_all(root)
    for profile, expected in PRIMARY.items():
        rows = files[profile+".jsonl"]
        require(len(rows) == expected, f"Missing primary {profile}")
        for row in rows:
            m = row["instance"]
            require(len(m["demand"]) == m["I"]*m["T"], f"Invalid instance dimensions: {row['key']}")
            if row["status"] == "SOLVER_VALIDATED":
                r = row["menu"]["result"] if profile == "capacity" else row["result"]
                validate_success(r, row["verification"], row["key"])
    require(len(files["external_reference.jsonl"]) == 168, "Missing external comparison runs")
    for row in files["external_reference.jsonl"]:
        if row["result"]["status"] == "SOLVER_VALIDATED":
            validate_success(row["result"], row.get("verification"), row["key"])
    external_pairs = {}
    for r in files["external_reference.jsonl"]:
        external_pairs.setdefault((r["profile"], r["key"]), {})[r["method"]] = r["result"]
    require(len(external_pairs) == 84, "External pairing incomplete")
    for pair in external_pairs.values():
        require(set(pair) == {"xopt", "literature"}, "Missing external pair member")
        a,b = pair["xopt"],pair["literature"]
        require(a["status"] == b["status"], "External status disagreement")
        if a["status"] == "SOLVER_VALIDATED":
            require(abs(a["objective"]-b["objective"]) <= 1e-5, "External objective disagreement")
    for profile, n in {"extended":90,"compound":128,"capacity_stress":32,"timing_repairs":6}.items():
        rows = files["revision_"+profile+".jsonl"]
        require(len(rows) == n, f"Missing revision {profile}")
        for row in rows:
            if row.get("output"):
                validate_anytime(row["output"], row["key"])
    studies = {name:study(files,name,n) for name,n in STUDIES.items()}
    for prefix in ("audit_long", "audit_sparsity"):
        for row in studies[prefix]:
            validate_anytime(row["output"], row["key"])
    for prefix in ("audit_margin", "levers_bench", "uc_bench"):
        for row in studies[prefix]:
            if row["result"]["status"] == "SOLVER_VALIDATED":
                validate_success(row["result"], row.get("verification"), row["key"])
    for row in studies["audit_naive"]:
        if row["correct"]["status"] == "SOLVER_VALIDATED":
            validate_success(row["correct"], row.get("correct_verification"), row["key"])
        # The deliberately incorrect nominal-capacity oracle is a negative control.
        if row["naive"]["status"] == "SOLVER_VALIDATED":
            require(isinstance(row.get("naive_verification", {}).get("valid"),bool), "Missing naive negative-control verification")
    enum_levers = validate_enum_cases(studies["levers_enum"], "levers", 40)
    effective_uc = apply_uc_correction(studies["uc_enum"], root)
    enum_uc = validate_enum_cases(effective_uc, "UC with explicit correction", 140)
    historical_disagreements = sum(r["enumeration"]["status"] == "OPTIMAL" and abs(r["dual"]["objective"]-r["enumeration"]["objective"]) > 1e-6 for r in studies["uc_enum"])
    require(historical_disagreements == 1, "Unexpected historical UC discrepancy count")
    radii = current_radii(root)
    require(len(radii) == 50 and len({r["key"] for r in radii}) == 50, "Missing/duplicate current radius records")
    for row in radii:
        radius = row["radius"]
        require(radius["status"] in ("NUMERICAL_BRACKET", "NUMERICAL_CLIPPED"), f"Unresolved radius: {row['key']}")
        require(0 <= radius["lower"] <= radius["upper"] <= .25+1e-5, "Invalid radius interval")
        require(row["mode"] != "strong" or radius["lower"] > 0, "Strong witness lost positive radius")
    require(len(files["single_lever.jsonl"]) == 108, "Missing coordinate-baseline records")
    for row in files["single_lever.jsonl"]:
        if row["status"] == "RESTRICTED_SOLVER_OPTIMAL":
            require(row.get("verification", {}).get("valid") is True, "Invalid coordinate baseline")
    fresh = validate_current_report(root, files)
    return {"passed":True,"historical_records":sum(len(v) for v in files.values()),
            "primary_runs":320,"external_comparison_runs":168,"supplementary_retained_attempts":256,
            "study2_records":1216,"study3_records":250,"study4_records":300,
            "raw_files_verified":len(downloads),"pglib_files_verified":4,
            "levers_enumeration":enum_levers,"uc_enumeration":enum_uc,
            "historical_uc_disagreements_preserved":historical_disagreements,"uc_corrections":1,
            "radius_audits":len(radii),"fresh_current_validation":fresh,
            "source_policy":"Historical hashes verified against preserved original code; current numerical checks bound separately",
            "arithmetic":"Float64/tolerance-based checks with the same solver; no rational proof certificates",
            "campaigns_recomputed":False}


def checked_report_output(root, output=None):
    """Keep report writes separate from allowlisted inputs and their file aliases."""
    root = Path(root).resolve()
    default = root / "experiments/results/validation_report.json"
    destination = Path(output).absolute() if output is not None else default
    require(not destination.is_symlink(), f"Unsafe output symlink: {destination}")
    for parent in destination.parents:
        if parent == root:
            break
        if parent.is_relative_to(root):
            require(not parent.is_symlink(), f"Unsafe output symlink parent: {destination}")
    manifest = checked_path(root, "experiments/docs/publication_allowlist.json")
    document = json.loads(manifest.read_text())
    names = document.get("files", []) + document.get("optional_pdf", [])
    protected = {manifest, root / "experiments/provenance/frozen_manifest.json"}
    for name in names:
        if name == "experiments/results/validation_report.json" and destination == default:
            continue  # Only the normal report path is a refreshable generated output.
        protected.add(checked_path(root, name))
    if destination != default:
        protected.add(default)
    resolved = destination.resolve()
    require(destination == default or not destination.exists(),
            f"Unsafe output: custom report must use a new path: {destination}")
    for source in protected:
        collision = resolved == source.resolve()
        if not collision and destination.exists() and source.exists():
            collision = destination.samefile(source)  # Hardlinks also alias input bytes.
        require(not collision, f"Unsafe output would replace a protected input: {destination}")
    require(not destination.exists() or destination.is_file(), f"Output is not a regular file: {destination}")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        output = checked_report_output(args.root, args.output)
        report = validate(args.root)
    except (ValueError,KeyError,OSError,TypeError) as error:
        parser.exit(1, f"Artifact validation failed: {error}\n")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
