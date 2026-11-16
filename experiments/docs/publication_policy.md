# Public distribution policy

The editable manuscript belongs to the author and stays local. General permission
to publish the project or its MIT experimental code does not authorize publishing
LaTeX, bibliographies, templates, Word files, manuscript tables or editable figure
sources. This boundary applies to branches, tags, their reachable history,
releases, attached files, source ZIPs and other public services. An ordinary
commit deleting a private file does not remove it from earlier commits.

The current distribution allowlist is `experiments/docs/publication_allowlist.json`.
Its `files` array contains individual repository-relative file names. It is a
reviewed input, not a directory/glob discovery rule: new files receive no automatic
authorization. Numerical CSV/JSON results, computational code, public source data
and the listed historical computational snapshots are authorized categories;
`article/`, local editorial evidence, scratch research, partial writes and old
release/superseded correction backups are absent. The three explicitly preserved
20261024 correction records and the separately named 20261028 verification outputs
are distinct entries, together with their required source provenance. The root `.gitignore` adds portable protection to clones, but ignores
cannot remove files that are already tracked and do not replace this validator.

The original local resource report `experiments/results/resources_20261017.json`
and the six historical `experiments/results/levers_logs/bench_w*.log` files contain
personal filesystem paths and remain private, unmodified. Their omission does not
modify the frozen JSONL records. The logs document interrupted processes, so their
absence from the public candidate is a limitation of that candidate's provenance.
The validator also rejects common macOS and Linux personal filesystem paths in file
content; this bounded check is not a complete detector of sensitive information.

The author sign-off, internal correction and manuscript plans, internal scientific
and code-review notes, research log and `experiments/research/` are private. Their
historical copies in the original local provenance objects are private too. The
validator rejects these named paths even when they are listed, present in a ZIP or
reachable from a Git ref. This is a defensive list, not a substitute for human review
of every allowed file or a complete detector of renamed content.

The default ZIP contains no paper PDF. The sole optional PDF name is
`article/main.pdf`. Add `--include-paper-pdf` to both commands only after explicit
author authorization to distribute that PDF; the flag records inclusion, not
proof that permission was granted. It never enables manuscript source files or
other PDF attachments. Recognizable PDF content under another file name is also
rejected; the optional PDF must have a PDF header.

## Local review commands

Run from the project root. First make a new public-only snapshot outside the project.
The original retrospective provenance manifest and all original records stay local;
the snapshot's explicitly labelled manifest is a projection that omits private
source objects while preserving every historical record and the source identities
actually cited by those records. The script checks record hashes and refuses a
projection that would omit a cited source. Never label this projection as an
identical copy of the complete original manifest.

```sh
python3 -m unittest discover -s experiments/test -p 'test_*.py' -v
python3 experiments/scripts/prepare_public_snapshot.py --output /tmp/xopt-public-snapshot
python3 experiments/scripts/build_release.py --root /tmp/xopt-public-snapshot \
  --output /tmp/xopt-code-candidate.zip --report /tmp/xopt-candidate-build.json
python3 experiments/scripts/validate_publication.py --root /tmp/xopt-public-snapshot \
  --archive /tmp/xopt-code-candidate.zip --report /tmp/xopt-archive-validation.json
```

These commands build and inspect local artifacts. They do not upload anything,
change the index, rewrite Git history, create releases or establish readiness for
journal submission. Public upload requires a separate explicit instruction. Use
`--root` and `--manifest` to validate a different prepared checkout. Copy only the
ZIP's explicit file set into a fresh prospective public checkout, then inspect all
refs in that checkout before pushing: a clean ZIP alone does not sanitize a Git push.
The existing working repository contains private history and must not be pushed as
a clean replacement. A new candidate is not an already published version.

The builder reads only the listed inputs, checks reachable Git history when the
root is a Git checkout, writes a temporary ZIP, verifies its exact contents and
per-file SHA-256 values, and then installs the candidate archive. It includes
`experiments/release_manifest.json` with exact names, sizes and hashes. Its bytes
are deterministic for the same input bytes and optional-PDF choice. An invalid
input leaves an existing output untouched. Destination symlinks and report paths
(including hardlink aliases) that would overwrite an input, the allowlist or the
candidate archive are rejected.
Release metadata must agree with the schema and actual PDF/manuscript policy.

ZIP inspection is recursive, without extracting files. It rejects private
extensions/paths, recognizable renamed manuscript/Word packages, symlinks,
traversal and absolute paths, duplicate members, encrypted members, opaque backup
formats and excessive expansion/nesting. The public UCI retail ZIP is an explicit
data exception with one listed member, `Online Retail.xlsx`; the XLSX's XML
package is inspected as well. Other nested archives are forbidden; adding another
data-archive exception requires a reviewed policy change and explicit file/member
names. This is a boundary check, not an exhaustive content or secrets audit; human review of every new allowlist entry remains necessary.

Historical source objects have explicit names in the allowlist. Their SHA-256
file name must match their bytes and a safe original computational path in
`experiments/provenance/frozen_manifest.json`. Arbitrary objects under a hash name
receive no authorization. The snapshot's date and retrospective provenance limits
remain as documented in that manifest; preserving an old computational source is
not an assertion that it was correct. The separately preserved 20261024 correction
source objects are likewise mapped and verified against
`experiments/provenance/corrections_20261024/manifest.json` in files and every Git
tree; an object with a missing, private or mismatched source identity is rejected.

The Git scan checks every locally reachable commit from every local ref,
including remote-tracking branches and tags, plus detached HEAD. It checks each
tree path, blob and nested ZIP, including direct tree refs used by local
checkpoints. Unnamed blob refs, submodules and symlinks fail
closed. An untracked local private manuscript is expected and is never included
by the constructor. Reflogs/unreachable objects, remote refs not fetched into the
checkout, hosted release assets, caches, forks and third-party downloads are
outside this local check.

The hosted workflow inspects the tree of the commit under test and the archive
built from it. It does not scan earlier commits: the public repository keeps its
history, and commits up to version 1.0.2 contain internal documents listed above,
so a full-history scan of a complete clone is expected to fail there.

## If a public source leak is found

Keep a local private backup before any corrective operation. Identify every
public ref and attached archive containing it, construct a clean distribution by
this explicit allowlist, and obtain authorization for any required destructive
history/release correction. Verify the hosted refs, archives and known old URLs
afterwards. Record what was checked and acknowledge that caches, forks and
previous downloads cannot be conclusively purged by a local Git operation. No
purge, remote rewrite, new release or public upload is performed by these tools.
