#!/usr/bin/env python3
"""Build a deterministic, explicit-allowlist ZIP locally, without publishing it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from validate_publication import (PolicyError, RELEASE_MANIFEST, common_arguments,
                                  load_manifest, protect_destinations, validate, write_report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    common_arguments(parser)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    temporary = None
    safe_report = None
    try:
        protect_destinations(args.root, args.manifest, report=args.report, output=args.output)
        safe_report = args.report
        args.root = args.root.resolve()
        args.output = args.output.resolve()
        document, payloads = load_manifest(args.root, args.manifest,
                                           include_paper_pdf=args.include_paper_pdf)
        if args.output in [args.root / name for name in payloads]:
            raise PolicyError("output cannot replace an allowlisted input")
        has_git = (args.root / ".git").exists()
        report = validate(args.root, args.manifest, include_paper_pdf=args.include_paper_pdf,
                          check_history=has_git)
        history = report["git_history"]
        generated = {"schema": 1, "files": [
            {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(payloads.items())],
            "paper_pdf_included": report["paper_pdf_included"],
            "editable_manuscript_sources_included": False}
        payloads[RELEASE_MANIFEST] = (json.dumps(generated, indent=2) + "\n").encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".xopt-release-", suffix=".zip",
                                         dir=args.output.parent, delete=False) as file:
            temporary = Path(file.name)
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(payloads.items()):
                entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, data)
        report = validate(args.root, args.manifest, include_paper_pdf=args.include_paper_pdf,
                          archive=temporary)
        temporary.replace(args.output)
        temporary = None
        report.update({"archive": str(args.output), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                       "git_history": history, "published": False})
    except (PolicyError, OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        if temporary:
            temporary.unlink(missing_ok=True)
        report = {"valid": False, "published": False, "error": str(error)}
        write_report(safe_report, report)
        print("Publication policy rejected: " + str(error), file=sys.stderr)
        return 1
    write_report(safe_report, report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
