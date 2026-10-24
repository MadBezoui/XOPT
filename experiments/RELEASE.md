# XOPT v1.0.2 — corrected research artifact

[Repository](https://github.com/MadBezoui/XOPT) · [Frozen original release v1.0.1](https://github.com/MadBezoui/XOPT/releases/tag/v1.0.1) · [Original version DOI](https://doi.org/10.5281/zenodo.23472314) · [Current state](docs/current_status.md)

Version **1.0.2** publishes the corrections of 24 October 2026. Version 1.0.1 remains available as the original archive. Version 1.0.2 does not rerun every campaign: the original records are kept and the corrections are separate, explicitly bound outputs.

## What changes in 1.0.2

The supported implementation corrects witness-domain checks, shared support budgets, option validation, UC competitor-dual bounds and future enumeration deadlines. Shared launchers limit concurrency without changing historical shard identities and propagate child failures. The final gate covers every study and checks correction/provenance consistency.

All 43 original JSONL files (2,668 records) remain unchanged. The retrospective pre-correction computational snapshot is bound by `experiments/provenance/frozen_manifest.json`; original source bytes are stored by hash under `experiments/provenance/objects/`. It contains no editable manuscript sources and does not create missing execution-time provenance.

One new UC record corrects the known objective from `0.252853612595` to `0.204387890099`, explicitly linked to its original attempt. Analyses distinguish historical 139/140 from effective 140/140 agreement. Fifty main-study radii are recalculated separately, and current-code witness checks have their own report. None of this silently replaces the original records or implies all campaigns were rerun. Historical enumeration overruns remain disclosed.

The manuscript positioning acknowledges Wang (2013) and Ley–Merkert (2025). The user-supplied Wang PDF has now been read in full (16 pages, printed pages 491–506), and the formal comparison recognizes its general polyhedral target, editable continuous-variable costs, duality/complementarity reformulations and exact separation/branch-and-bound framework. Claims concern the structured pattern-dual approach, proved constants, temporal groups/budgets and the measured computational evidence. No Wang implementation or matched runtime experiment was run; the author must still assess scientific originality. The detailed local report, `article/wang_comparison_20261024/comparison.md`, and the supplied source PDF stay private under `article/` and are absent from computational distributions.

## Reproduction and review artifacts

The standard `reproduce.sh --no-pdf` path performs replay, tests, targeted corrections, current witness checks, analyses and the final gate. `--recompute` requires a new `XOPT_RESULTS_DIR` outside historical results and creates separate driver-campaign attempts. It does not compute radii for those new witnesses: the 50 historical radii are recalculated by the separate replay step. New record counts and statuses may differ; no 2,668-record new campaign is asserted. See the [computational guide](README.md) for commands and the [correction addendum](docs/correction_protocol_20261024.md) for conditions. Actual check counts and outcomes come from the generated reports, not this release note.

A local release candidate must be built from the explicit publication allowlist and verified recursively, including nested archives and reachable Git references. Editable LaTeX, bibliography, templates, Word and manuscript sources remain local. An optional paper PDF requires its own authorization. A candidate archive or a passing validator does not publish it; no upload, push or deposit is part of these corrections.

## Licenses and historical distributions

Original code remains under MIT; data and dependencies retain their licenses. See [license scope](LICENSING.md). Public version 1.0.0 included CE4IO v1.1 under its original AGPL-3.0-only terms. Version 1.0.1 removed those bundled files and retained provenance. That removal did not withdraw the still-accessible 1.0.0 copies or downloaded copies, and is not a legal opinion about licensing obligations.
