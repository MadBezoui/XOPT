> Historical record of the initial research revision. The subsequent six-point review is addressed in `article/revision_response.md`; current numerical statuses and evidence are documented in `experiments/README.md` and the current result files. Earlier terminology and counts below describe the archived version.

# Revue technique — portée et preuves

La relecture indépendante du cadrage a été effectuée et a produit `scientific_audit.md`. La relecture indépendante finale du code n'a pas abouti (limite de quota du sous-agent). Elle n'est pas présentée comme acquise. La revue du code a donc été poursuivie par l'agent principal, avec les contrôles exécutables ci-dessous.

- Produit coût × activation : quatre contraintes exactes avec variable binaire, bornes symétriques explicites.
- Recours continu : coûts fixes au sein d'un scénario ; chaque motif oracle fournit un intercept de recours valide.
- Epsilon présent dans chaque coupe, marge forte négative sur le membre droit, oracle fort limité au complément du foil.
- Complément de plusieurs littéraux : somme des violations >=1, testé contre énumération.
- Capacité : pools distincts, intervention tarifée dans l'objectif, union des supports temporels, limite globale du menu.
- Statuts : seules les résolutions adéquates produisent les certificats ; timeouts ne deviennent pas des infaisabilités.
- Valeurs sauvegardées : reconstruction indépendante depuis JSONL (ordre colonne Julia), contrôles des équations, bornes, objectifs et nouvel oracle sur chaque témoin effectif, y compris menu.
- Résultats : accords sur 20 paires exhaustives, tests analytiques, 78 assertions principales + 3 sur rayon ; aucune validation sauvegardée en échec.
- Rayon : coût de la trajectoire retenue, non confusion avec le recours minimum ; borne inférieure oracle pour côté sûr ; bord de rayon ne garantit qu'une non-infériorité, strict à l'intérieur.
- Baseline simple : minimum sur une coordonnée explicitement distingué du minimum global ; tous les résultats positifs vérifiés par nouvel oracle.

Limites connues : modèles construits, 1 thread, machine partagée, warmup faible uniquement (compilation résiduelle possible), pas de répétitions de timings, pas de comparaison externe d'état de l'art, mémoire limitée. Les fonctions publiques sont conçues pour les domaines documentés : quantités non négatives, rétention dans [0,1], capacités positives et foil binaire. Ne pas appliquer les bornes d'état à une dynamique de croissance supérieure à 1 sans adaptation.
