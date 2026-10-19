# XOPT: sparse temporal counterfactual explanations for mixed-integer planning

This repository holds the code, data and result records of the article "Sparse temporal counterfactual explanations for mixed-integer planning: recourse duality, complexity and stability". The archived versions are on Zenodo, https://doi.org/10.5281/zenodo.23458561, which resolves to the latest version. The French README gives the same information in more detail.

## Layout

- `experiments/src/` holds the Julia modules. `XOPT.jl` builds the lot-sizing and workforce models, the forward oracle, cost constraint generation (CCG) with its multicut variant and the capacity menus. `anytime.jl` adds initialization and gap reporting, `robustness.jl` the stability radius, `levers.jl` the recourse-cost levers, `uc.jl` the unit commitment model, `literature_cg.jl` the reimplementation of Engelhardt et al., and `audit.jl` the naive capacity handling and the coordinate bound. `enumerate_levers.jl` and the enumeration part of `uc.jl` are independent references for small instances.
- `experiments/scripts/` holds the experiment drivers (`run_*.jl`), the launchers of Studies 2 to 4 (`launch_*.sh`), the analysis scripts (`analyze*.py`) and `reproduce.sh`.
- `experiments/test/` holds the tests, `experiments/docs/` the protocols of every study and the research log, `experiments/results/` the result records, and `experiments/research/` the exploratory runs cited in the research log.
- `data/` holds the retail and hospital inputs with their checksums, and `experiments/data/pglib_uc/` the unit commitment inputs (see `PROVENANCE.md`).

## Reproducing the results

Install Julia 1.11 and Python 3.11 or 3.12, create the Python environment as `.venv` at the root or outside the tree (the artifact check rejects other root folders), then `pip install -r experiments/requirements.txt`, and run from the repository root

```
bash experiments/scripts/reproduce.sh
```

The script instantiates the Julia environment from the lockfile, runs the tests, all experiments and all analyses, and rebuilds the tables and figures. Studies 2 to 4 run several single-thread jobs at once and take several hours. Timings depend on the machine, while objective values and checks should agree within the stated tolerances. The drivers reuse the archived records, so on the archive the script mainly reruns tests and analyses. To recompute a study, move its records in `experiments/results/` aside first, or set the environment variable `XOPT_RECOMPUTE=1` for the external comparison, the stability radii of `run_robustness.jl` and the one-coordinate baseline.

## Licenses

The code is under the MIT license (`experiments/LICENSE`). The input data keep their own licenses: CC BY 4.0 for the UCI and PGLib-UC data (`experiments/data/pglib_uc/LICENSE`) and the Open Government Licence for the NHS data.
