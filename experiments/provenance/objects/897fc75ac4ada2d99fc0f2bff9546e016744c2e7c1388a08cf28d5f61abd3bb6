> Historical record of the initial research revision. The subsequent six-point review is addressed in `article/revision_response.md`; current numerical statuses and evidence are documented in `experiments/README.md` and the current result files. Earlier terminology and counts below describe the archived version.

# XOPT: design scientifique et expérimental

Date de référence: 16 octobre 2026. Cible conservée: EJOR, sous réserve d'une validation de nouveauté et d'adéquation éditoriale.

## Objectif
Transformer un manuscrit non validé en dossier de recherche reproductible. Trois répertoires racine seulement: article, experiments, data. Préserver intégralement la version originale dans article/archive.

## Décisions de conception
- Modèles temporels mixtes avec décisions d'activation binaires, quantités et états continus; aucune prétention générale sur la complexité sans preuve.
- Perturbations continues bornées des coûts d'activation, sur variables binaires seulement: produits exactement linéarisables. Capacités modifiables sur un menu fini explicite d'interventions, résolues séparément. Aucune comparaison de trajectoires provenant de capacités différentes.
- Oracle MILP exact pour vérifier les foils partiels. CCG sur chaque scénario de capacité avec coupes de trajectoires valides. Baseline exhaustive des motifs binaires sur petites instances. Variante de génération de coupes par plusieurs trajectoires comme ablation; pas de revendication de décomposition temporelle séparant des états couplés.
- Explications faibles, epsilon-optimales, et fortes avec marge positive explicite: comparaison avec le meilleur compétiteur hors foil.
- Données publiques réelles compactes pour demandes de commerce et activité hospitalière; coûts, capacités et paramètres opérationnels construits et identifiés comme tels. Pas de validation clinique ni de prétendue étude utilisateur.
- Julia/JuMP/HiGHS pour modèles et calculs. Acquisition/figures auxiliaires autorisées en Python. Versions, SHA-256, provenance, configurations, journaux et statuts archivés.
- Résultats calculés uniquement; timeouts conservés; pas de supériorité annoncée avant comparaison. Pilotage et étude principale explicitement distingués si l'échelle ne permet pas des conclusions générales.

## Livrables
Code Julia testable, données et manifestes, configurations et scripts de reproduction, résultats machine et tableaux/figures générés, manuscrit corrigé compilé, audit scientifique, instructions en français et liste des conditions de soumission restantes.

## Validation
Tests de conservation/foils/produits; comparaison CCG contre énumération complète sur petits cas; vérification indépendante des explications à paramètres figés; comparaison à budget et matériel identiques; analyse appariée des temps, taux de certification, parcimonie et marges; contrôle bibliographique et compilation LaTeX.
