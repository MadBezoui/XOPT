# XOPT audit corrections implementation plan

> **For agentic workers:** use systematic debugging, test-driven development and verification-before-completion. Independent domains are delegated concurrently; integration and final verification are performed by the primary agent.

**Goal:** resolve audit findings A01–A12 while preserving original observations, historical attempts, manuscript privacy and truthful scientific claims.

**Architecture:** keep historical JSONL immutable and bind their original code through a content-addressed computational snapshot. Add explicitly identified numerical corrections and fresh validations, and distinguish historical source verification from current-code validation. Build public artifacts only from a checked explicit allowlist.

**Tech stack:** Julia 1.11.6, JuMP/HiGHS, Python 3.11 with pinned direct dependencies, LaTeX.

**Spec:** private audit `article/audit_20261024.md` and its twelve findings. No public upload, Git reset, or manuscript-source publication is part of this task.

## Global constraints

- Preserve all 2,668 historical JSONL records byte for byte.
- Preserve pre-existing user edits and the original audit evidence.
- Keep TeX, bibliography, templates, Word and editable manuscript assets local.
- Distinguish solver tolerances, admissibility, optimality, unresolved outcomes and exact mathematical results.
- Use one or two Julia processes at most during integration; configurable campaign launchers default to bounded concurrency.

## Review focus

- Fractional, nonfinite or incorrectly shaped witness arrays must be rejected before rounding or solver invocation.
- Distinct cost types in one cell count as distinct parameters; capacity edits share the period budget.
- Historical source hashes must resolve to the frozen original bytes, never be rewritten to current hashes.
- Missing or invalid study records must cause final validation failure; known historical errors require explicit corrections.
- Every public archive and reachable Git ref must be free of editable manuscript material, including nested archives.

## Tasks

1. **Julia correctness (A02,A03,A06,A07,A08).** Add failing regression tests from the audit fixtures; fix dual bounds, witness validation, option checks and enumeration deadlines. Run the targeted tests and six complete suites. Record the corrected UC case separately, retaining the old attempt.
2. **Publication boundary (A05).** Add portable exclusions, explicit file allowlist, archive builder and recursive publication/history validator. Exercise real archive and Git fixtures containing forbidden files, nested archives and traversal/symlink cases. No upload or public Git operation.
3. **Scientific text (A01,A10,A12).** Verify primary references, map the partial inverse MILP antecedents, narrow novelty, qualify weak-radius claims and update current author-facing documents. Record full-text access limits honestly; do not invent author attestations or publication of corrections.
4. **Provenance and global gate (A04,A09,A11).** Add source resolution against frozen objects, comprehensive per-study validation, corrected-result overlays and fresh radius records binding all producing modules and inputs. Test missing cases, false validation flags, modified snapshots and absent corrections. Relocate loose local working documents without deleting them.
5. **Integration.** Update replay/recompute commands and metadata, bound launcher concurrency, run fresh witness checks, regenerate tables/figures, compile and inspect the PDF. Build and inspect an allowlisted local release candidate; do not publish it.
6. **Closure.** Write a per-finding resolution ledger with commands, counts, artifacts and any remaining scientific/editorial limits. Verify historical hashes and manuscript exclusions again before reporting completion.

No commits are created automatically: the initial worktree contains substantial user-owned changes and a local Git base behind the equivalent public file tree.
