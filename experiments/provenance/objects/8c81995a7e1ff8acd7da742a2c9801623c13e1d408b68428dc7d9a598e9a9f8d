> Protocol addendum after scientific review: all primary experiments are rerun with lower-bound stopping and qualified solver statuses. The matched literature comparison adds 84 paired queries (168 supplementary runs); see `external_comparison.md`. Exact-arithmetic theorems are distinguished from Float64 numerical validation.

# Protocole exécuté

Les données réelles sont transformées en benchmarks semi-synthétiques, pas en modèles opérationnels validés.

- Retail: toutes transactions positives à prix positif, hors annulations et codes non-produits; agrégation par semaine complète. Sélection de 30 références sur janvier–mars 2011 uniquement; expériences sur avril–novembre; normalisation par moyenne des 13 semaines de calibration.
- NHS: Type 1 A&E attendances mensuelles 2024–25, 30 providers complets sélectionnés par volume d'avril. Évaluation à partir de mai, normalisation par avril. Charge utilisée dans un modèle hypothétique de mobilisation d'effectifs persistants; aucune attente de patients sur des mois, aucun modèle clinique ICU.
- Coûts d'activation Uniforme[2,3] avec MersenneTwister(seed); coût de quantité 0.25, stockage 0.2 ou effectifs 0.5, rétention hospitalière 0.8; capacité 1.4 fois le maximum de demande agrégée de la fenêtre. Calibration capacité sur horizon complet: benchmark déterministe, pas prévision hors-échantillon.
- Foil: inverser un bit de la solution nominale; item et période choisis déterministement avant résolution de l'explication. Aucune sélection a posteriori de foils faciles.
- Coûts modifiables de ±80%; parcimonie temporelle 0.01 par période, somme relative L1 et budget de périodes. Marge forte 0.02 par défaut. Epsilon additif, non appelé relatif.
- Méthodes: CCG global; multicut (3 motifs max/itération); énumération intégrale de motifs et LP de recours pour petits cas. Aucun solveur de la littérature n'est prétendu reproduit.
- Correction: 40 exécutions, 2 familles × 5 seeds × 2 régimes × 2 méthodes, I=2,T=4, 30 s/méthode.
- Comparaison principale: 120 exécutions, 2 familles × 3 tailles × 5 seeds × 2 régimes × 2 méthodes; tailles (1,4),(2,6),(3,8); 15 s/méthode.
- Sensibilité: 72 exécutions, 2 familles × 4 seeds × budgets K={1,2,6} × régimes faible/epsilon=.1/fort gamma=.1; 15 s.
- Échelle: 36 exécutions, 2 familles × tailles (5,8),(5,11),(10,11) × 3 seeds × 2 régimes; 20 s.
- Capacités: 16 exécutions, 2 familles × 4 seeds × 2 régimes; menu nominal + hausse de 25% sur chacune des six périodes, K=3, limite totale 30 s.
- Précompilation et warmup exclus; temps de construction et de tous les sous-problèmes inclus, oracle de validation indépendant exclu et signalé. HiGHS utilise un seul thread. Ordre des jobs permuté avec seed 20261016; machine partagée, absence de répétitions de chronométrage explicitée.
- Statuts timeouts, infaisables et non certifiés conservés. Temps moyens sur certifiés accompagnés du dénominateur; statistiques appariées seulement sur intersection explicitée. Agrégation descriptive; pas de test iid trompeur sur fenêtres partageant les données.
- Les programmes interrompent et enregistrent un statut inconnu/limite de temps; ils ne convertissent pas un échec de solveur en certificat d'infaisabilité.

Extensions exécutées : 12 horizons longs retail (5,24)/(10,32), 24 foils à deux littéraux, 108 baselines à une coordonnée et 50 rayons de stabilité. La baseline et les rayons sont analysés séparément des 320 runs principaux. Le warmup initial porte sur le mode faible ; des compilations de branches peuvent subsister dans les premiers timings forts.
