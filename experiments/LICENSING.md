# License scope

The original Julia, Python and shell code in this project is available under the
MIT license in [LICENSE](LICENSE), as authorized by Madani Bezoui on 17 October
2026. This includes the independently implemented literature comparator.

This code license does not relicense the following materials:

- The manuscript, figures and scientific prose remain subject to the author's
  publication and reuse decisions. Public access does not imply journal acceptance
  or a separate Creative Commons license for the manuscript.
- UCI Online Retail retains its CC BY 4.0 license and attribution to Daqing Chen.
- NHS England releases retain their Open Government Licence terms and attribution.
  See [`data/README.md`](../data/README.md) and the source manifest for data provenance.
- The PGLib-UC case files in `experiments/data/pglib_uc/` retain their CC BY 4.0 license.
  See [`PROVENANCE.md`](data/pglib_uc/PROVENANCE.md).
- Third-party LaTeX templates are retained only in the author’s local manuscript sources and are excluded from the public distribution.
- Julia and Python dependencies retain their own licenses.
- The inspected CE4IO archive is AGPL-3.0-only. Its implementation is not bundled
  in public versions 1.0.1 and 1.0.2, and is not imported by our comparator; provenance and the link to
  the original archive are provided for inspection.
- Release v1.0.0 contained an unmodified copy of the CE4IO v1.1 archive and five
  extracted files under AGPL-3.0-only. Release v1.0.1 removed them; the older public distribution and previously downloaded copies are not thereby withdrawn.

Only public source observations and explicitly described constructed parameters
are used in the experiments. The numerical results do not constitute exact MILP
proof certificates.

The 24 October 2026 corrections are published as version 1.0.2. The DOI
10.5281/zenodo.23472314 identifies the original version 1.0.1.

Editable manuscript sources (LaTeX, bibliography, templates, Word and other
article sources) remain local and must be excluded from all public Git history,
branches, tags, releases, attachments and archives. A general permission to
publish experiment code under MIT does not authorize these sources. Public
distributions must be assembled from an explicit checked allowlist, with nested
archives inspected. An authorized PDF is a separate distribution decision.

The content-addressed objects in experiments/provenance/objects preserve only
identified pre-correction computational files with their existing license scope.
The snapshot was captured retrospectively; preserving a source byte does not
establish missing execution-time provenance or confer a new license.
