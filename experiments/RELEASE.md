# XOPT v0.3.0-review — research artifact

[Repository](https://github.com/MadBezoui/XOPT) · [Versioned release](https://github.com/MadBezoui/XOPT/releases/tag/v0.3.0-review) · [Start here](README.md)

This release accompanies “Sparse temporal counterfactuals for mixed-integer optimization: Recourse reduction, numerical validation, and cost stability.” It contains the manuscript PDF (editable manuscript sources are excluded), attributed public raw inputs, processed panels, a pinned Julia environment, numerical methods, tests, full current result records and figure/table generators. Only three directories are present at the root: `article`, `experiments`, and `data`.

The original code is MIT-licensed as authorized by the author on 17 October 2026. See [LICENSE](LICENSE) and [LICENSING.md](LICENSING.md) for scope. UCI and NHS inputs retain their own licenses. The inspected CE4IO author implementation is not redistributed; its source archive is identified in `vendor/provenance.json`. The comparator is a separately written implementation of the published cost-edit algorithm, sharing the physical model and forward solver with XOPT.

The 320 primary runs include 258 solver-validated explanations, 47 solver-reported infeasible queries and 15 timeouts. The additional external comparison covers 84 paired queries (168 runs), with matching statuses and a maximum explanation-objective difference below 9e-13. All unresolved outcomes are retained. Numerical checks use floating-point arithmetic and tolerances; they are not exact mathematical certificates.

This revision adds a separately implemented anytime extension, a prospectively documented 250-slot supplementary study plus six paired timing repairs, paired sensitivity displays, compound foils and capacity stress diagnostics. Primary numerical evidence remains unchanged. All 256 supplementary attempts, including four sleep-interrupted measurements and their six paired repeats, are retained. At 20 seconds, initialized CCG retains 16/18 checked explanations versus 2/18 for cold CCG; the baseline alone retains 18/18. See `docs/revision_results.md` for full denominators, gaps and limitations. All editable manuscript sources stay local; each public payload file is named explicitly in `docs/publication_allowlist.json`, and archive and Git-history checks block excluded sources.

The archive includes a per-file SHA-256 manifest at `experiments/release_manifest.json`. `SHA256SUMS` accompanies the archive and the separately downloadable manuscript PDF. From the directory containing the downloaded files, verify them with `shasum -a 256 -c SHA256SUMS`.

This is a research prerelease: scientific author review and journal-submission declarations remain outstanding. It does not claim peer review, journal acceptance, independent replication or an assigned DOI. See [author decisions](docs/author_signoff.md) and the [publication policy](docs/publication_policy.md).
