# XOPT — Contrefactuels temporels parcimonieux pour la planification mixte

XOPT étudie les changements de paramètres qui rendent optimale une propriété préférée dans un modèle de planification à activations binaires et recours continu. Il traite les coûts d'activation, certains coûts de recours et un menu fini de capacités, avec des budgets communs sur les paramètres et périodes modifiés.

**Version 1.0.2**, qui intègre les corrections du 24 octobre 2026. Toutes les versions sont archivées sur Zenodo, https://doi.org/10.5281/zenodo.23458561, qui renvoie à la plus récente. La version d'origine [1.0.1, DOI 10.5281/zenodo.23472314](https://doi.org/10.5281/zenodo.23472314) ne contient pas ces corrections. Voir [l'état courant](experiments/docs/current_status.md), [le protocole de correction](experiments/docs/correction_protocol_20261024.md) et [le guide en anglais](README.en.md).

## Organisation

| Emplacement | Contenu |
|---|---|
| `experiments/src/` | Modèles et oracles Julia, CCG, anytime, rayon de stabilité, leviers et engagement de centrales |
| `experiments/scripts/` | Pilotes, lanceurs à concurrence bornée, analyses et contrôles de reproduction |
| `experiments/test/` | Huit suites Julia et tests comportementaux Python |
| `experiments/docs/` | Protocoles datés, addendum de correction et état courant |
| `experiments/provenance/` | Empreintes historiques et objets de code originaux conservés |
| `experiments/results/` | Enregistrements historiques et synthèses dérivées |
| `experiments/results/corrections_20261024/` | Correction UC, recalculs des rayons et validation avec le code corrigé |
| `data/` | Entrées UCI/NHS et données prétraitées, avec provenance et SHA-256 |
| `experiments/data/pglib_uc/` | Cas publics d'engagement de centrales PGLib-UC |

Le module `uc.jl` est le chemin UC pris en charge ; `uc2.jl` conserve des variantes exploratoires. `literature_cg.jl` est une réimplémentation interne appariée du schéma publié, utilisant les modèles et le solveur du projet ; elle n'est pas une exécution indépendante du logiciel des auteurs.

## Environnement

Utiliser Julia 1.11 avec `experiments/Manifest.toml`, et Python 3.11 avec les versions directes fixées dans [requirements.txt](experiments/requirements.txt). HiGHS est installé par l'environnement Julia et ne nécessite pas de licence commerciale. Pour isoler Python :

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r experiments/requirements.txt
```

Les commandes suivantes se lancent depuis la racine. `JULIA_BIN` et `PYTHON_BIN` désignent chacun un exécutable, y compris lorsque son chemin contient des espaces. La compilation facultative du manuscrit local exige aussi LaTeX et `latexmk` ; l'artefact de calcul public ne contient pas ses sources éditables.

## Replay et validation courante

```bash
PYTHON_BIN="$PWD/.venv/bin/python" bash experiments/scripts/reproduce.sh --no-pdf
```

Le mode par défaut conserve les 43 fichiers JSONL historiques, soit **2 668 enregistrements**. Il instancie l'environnement, exécute les huit suites Julia et les tests Python, applique la correction UC ciblée et les 50 recalculs de rayon, revérifie les témoins avec le code corrigé, régénère les six analyses et atteint le contrôle global final. Les sorties ciblées UC/rayons peuvent être réutilisées seulement si les empreintes du code, des options et des entrées correspondent. Les contrôles de témoins de `validate_updates.jl` sont une validation courante distincte ; leur effectif et leur verdict sont consignés dans `current_validation.json`.

Le replay des analyses n'est pas une nouvelle exécution des campagnes. Les objets de `experiments/provenance/objects/` et `frozen_manifest.json` ont été capturés rétrospectivement avant correction : ils lient des octets conservés, sans reconstituer une provenance d'exécution qui manquait aux enregistrements anciens. Les 108 résultats à une coordonnée et les 50 anciens rayons conservent leurs limites de provenance initiales.

La correction UC garde l'ancienne tentative à 0,252853612595 et enregistre séparément 0,204387890099. L'analyse distingue 139/140 concordances historiques et 140/140 après cette correction identifiée ; elle ne prétend pas à 140 nouveaux calculs. Le recalcul des rayons ne remplace pas `robustness.jsonl`. Une validation de témoin établit son admissibilité et la comparaison de coûts, pas l'optimalité globale de chaque intervention.

Sans `--no-pdf`, le script peut aussi compiler le manuscrit lorsque ses sources locales sont disponibles. Un passage des tests ou une compilation ne vaut ni accord de l'auteur, ni attestation éditoriale, ni preuve rationnelle exacte.

## Relancer séparément les campagnes des pilotes

Choisir un **nouveau dossier de résultats**, hors du répertoire historique :

```bash
XOPT_RESULTS_DIR=/tmp/xopt-recompute-20261024 XOPT_WORKERS=2 \
  PYTHON_BIN="$PWD/.venv/bin/python" \
  bash experiments/scripts/reproduce.sh --recompute --no-pdf
```

Ce mode relance les campagnes des pilotes et calcule de nouvelles tentatives dans ce dossier distinct. Il ne calcule pas les rayons de nouveaux témoins : les 50 rayons historiques font partie de l’étape ciblée du replay, sur ses témoins d’origine. Le nombre et les statuts des nouvelles tentatives peuvent différer ; aucun total de 2 668 nouveaux enregistrements n’est promis. Il ne faut ni déplacer ni écraser les JSONL historiques, ni substituer les nouveaux résultats aux observations publiées. Les fenêtres de données et requêtes sont conservées selon les protocoles, mais les temps, issues de limites et trajectoires du solveur peuvent changer avec le code, le matériel et la charge. Les campagnes des pilotes peuvent être longues ; leur relance n'est pas nécessaire au replay standard.

`XOPT_WORKERS` est un entier strictement positif, égal à 2 par défaut, qui borne la concurrence des lanceurs. Les identifiants et nombres de shards historiques restent inchangés. Toute erreur d'un enfant produit un code d'échec, y compris lors d'une reprise. Les énumérations corrigées partagent une échéance globale ; historiquement, 41/140 références UC dépassaient les 300 secondes annoncées, avec un maximum de 6 581,36 secondes. Leurs durées sont conservées comme déviation de protocole et ne décrivent pas une comparaison sous délais égaux.

## Portée scientifique et statuts

Les observations UCI/NHS sont réelles ; coûts, capacités et foils de ces modèles sont construits. Le modèle hospitalier utilise des profils de charge, pas des trajectoires de patients. UC est un sous-système redimensionné à un nœud ; les leviers marginaux supposent le dispatch sans rampes. Les 96 calculs marginaux UC non résolus à 300 secondes restent des résultats négatifs.

`SOLVER_VALIDATED` indique une conclusion numérique du maître et une comparaison fondée sur la borne de l'oracle aux tolérances fixées. `FEASIBLE_*` conserve une explication admissible sans optimalité établie. `TIME_LIMIT` est un arrêt de calcul et peut conserver un incumbent lorsqu'il est rapporté ; ce statut ne prouve pas l'infaisabilité. `SOLVER_INFEASIBLE` est la conclusion numérique du solveur. Tous ces contrôles utilisent Float64 ; aucune preuve rationnelle MILP n'est exportée.

Le [positionnement courant](experiments/docs/scientific_positioning_20261024.md) reconnaît l'optimisation inverse partielle antérieure, dont Wang (2013) et Ley–Merkert (2025). Le PDF de Wang fourni par l'utilisateur a été lu intégralement : 16 pages, pagination imprimée 491–506. La comparaison formelle reconnaît sa cible polyédrique plus générale que nos littéraux binaires, ses perturbations des coûts continus et sa combinaison de dualité, complémentarité, séparation et branch-and-bound. Le périmètre étudié ici est la parcimonie temporelle, l'agrégation par motif et les constantes démontrées pour les recours traités, sans revendication de première méthode exacte générale. Aucune réimplémentation de Wang ni mesure de temps appariée n'a été réalisée ; l'appréciation de l'originalité scientifique reste du ressort de l'auteur. Le rapport détaillé local est `article/wang_comparison_20261024/comparison.md` ; le PDF fourni et ce dossier de lecture restent privés, hors des distributions de calcul.

## Licences et distribution

Voir [MIT pour le code](experiments/LICENSE), [le périmètre des licences](experiments/LICENSING.md), [la citation](CITATION.cff) et [la note de livraison](experiments/RELEASE.md). Les données gardent leurs licences propres. Les sources éditables du papier restent locales : LaTeX, bibliographie, modèles, Word et autres sources du manuscrit sont exclues des historiques, branches, tags, releases et archives publiques. Toute distribution publique est construite par liste explicite de fichiers autorisés et inspectée avant envoi. Les corrections présentes ne publient aucun nouvel artefact.
