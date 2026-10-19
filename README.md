# XOPT — Sparse Temporal Counterfactuals for Mixed-Integer Optimization

Ce dépôt contient le code source, les données de référence et les résultats expérimentaux pour le calcul et l'évaluation d'explications contrefactuelles parcimonieuses avec recours continu temporel sous contraintes mixtes en nombres entiers (MILP).

## Organisation du dépôt

- `experiments/src/` :
  - `XOPT.jl` : modèles, oracle MILP, algorithme CCG (génération de contraintes de coût, *cost constraint generation*), multicut, énumération exacte, menus de capacité et validation numérique.
  - `anytime.jl` : initialisation conditionnelle par baseline, conservation des incumbents validés, bornes UB/LB et écarts sous limite de temps.
  - `robustness.jl` : calcul du rayon de stabilité d'un témoin fixé.
  - `audit.jl` : calibration de marge, séparation par scénario et borne de coordonnée.
  - `levers.jl`, `enumerate_levers.jl` : leviers sur les coûts unitaires et de stockage avec coupes duales.
  - `uc.jl`, `uc2.jl` : modèle d'engagement de centrales (*unit commitment*) sur instances PGLib-UC.
  - `literature_cg.jl` : réimplémentation comparative indépendante de l'algorithme de génération de contraintes de la littérature.
- `experiments/scripts/` : scripts d'exécution des expérimentations, d'analyse statistique et de reproduction.
- `experiments/test/` : bancs de tests unitaires et de validation (Julia et Python).
- `data/` : données brutes et prétraitées (NHS hospitalier, Online Retail), avec métadonnées de téléchargement et sommes de contrôle SHA-256. Les instances PGLib-UC sont dans `experiments/data/pglib_uc/`.
- `experiments/results/` : jeux complets de résultats numériques (synthèses CSV et traces détaillées JSONL).
- [Licence MIT du code](experiments/LICENSE), [périmètre des licences](experiments/LICENSING.md) et [citation](CITATION.cff).

## Reproduction des résultats

### Prérequis

- Julia 1.11 avec l'environnement verrouillé par `experiments/Manifest.toml`.
- Python 3.11 avec les dépendances indiquées dans `experiments/requirements.txt`.
- Le solveur HiGHS (libre et intégré dans l'environnement Julia, aucune licence commerciale requise).
- Un environnement Python créé dans `.venv` à la racine du dépôt, ou hors du dépôt : le contrôle final (`validate_artifact.py`) refuse tout autre dossier visible à la racine.

### Lancement de la reproduction

Depuis la racine du dépôt :

```bash
bash experiments/scripts/reproduce.sh
```

Les pilotes réutilisent les enregistrements archivés, et le script relance alors surtout les tests et les analyses. Pour recalculer une étude, déplacez d'abord ses enregistrements hors de `experiments/results/`, ou définissez la variable d'environnement `XOPT_RECOMPUTE=1` pour la comparaison externe, les rayons de stabilité de `run_robustness.jl` et la référence à une coordonnée.

### Exécution des tests

```bash
julia --startup-file=no --project=experiments experiments/test/runtests.jl
julia --startup-file=no --project=experiments experiments/test/robustness.jl
julia --startup-file=no --project=experiments experiments/test/literature_reference.jl
julia --startup-file=no --project=experiments experiments/test/anytime.jl
julia --startup-file=no --project=experiments experiments/test/levers.jl
julia --startup-file=no --project=experiments experiments/test/uc.jl
```

## Études expérimentales

1. **Benchmark principal et révision anytime** :
   - 320 calculs principaux et 250 essais de révision temporelle (`experiments/results/all_results.csv`, `experiments/results/revision_results.csv`).
   - Analyses de sensibilité appariées et classification de capacité.

2. **Comparaison avec la littérature** :
   - 84 requêtes appariées (168 calculs) avec le schéma exact publié le plus proche (`experiments/results/external_summary.json`).

3. **Étude 2 — Audit et sensibilité** :
   - Protocole : `experiments/docs/audit_protocol_20261017.md`
   - Script : `experiments/scripts/run_audit.jl`
   - Résultats : `experiments/results/audit_*`

4. **Étude 3 — Leviers de coûts** :
   - Protocole : `experiments/docs/levers_protocol_20261017.md`
   - Script : `experiments/scripts/run_levers.jl`
   - Résultats : `experiments/results/levers_*`

5. **Étude 4 — Engagement de centrales (Unit Commitment)** :
   - Protocole : `experiments/docs/uc_protocol_20261017.md`
   - Script : `experiments/scripts/run_uc.jl`
   - Données : `experiments/data/pglib_uc/` (provenance dans `PROVENANCE.md`)
   - Résultats : `experiments/results/uc_*`

## Interprétation des statuts du solveur

- `SOLVER_VALIDATED` : le problème maître est déclaré optimal par le solveur et la borne inférieure rapportée par l'oracle satisfait la condition de comparaison à la tolérance déclarée. Chaque solution est ensuite vérifiée indépendamment par une résolution de contrôle.
- `FEASIBLE_TIME_LIMIT`, `FEASIBLE_UNRESOLVED` : une explication admissible a été identifiée dans le temps imparti mais l'optimalité globale n'est pas garantie.
- `SOLVER_INFEASIBLE` : conclusion d'infaisabilité du solveur dans le domaine autorisé.
- `TIME_LIMIT` : expiration du budget de calcul avant découverte d'une solution admissible.
