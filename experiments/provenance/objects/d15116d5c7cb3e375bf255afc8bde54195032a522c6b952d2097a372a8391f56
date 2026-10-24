> Historical record of the initial research revision. The subsequent six-point review is addressed in `article/revision_response.md`; current numerical statuses and evidence are documented in `experiments/README.md` and the current result files. Earlier terminology and counts below describe the archived version.

# Audit scientifique indépendant du projet XOPT

Date de référence : 16 octobre 2026. Documents examinés : `article/archive/main.tex` et `experiments/docs/design.md`. Cet audit évalue la cohérence du modèle et des revendications ; il ne constitue ni une validation des résultats numériques, ni une garantie de publication.

## Avis sur le design de remplacement

Le périmètre proposé est cohérent **si les coûts modifiés portent exclusivement sur des variables binaires, les contraintes et le coût du recours continu sont fixes dans chaque scénario, et les foils forts sont des propriétés des variables binaires**. Une génération exacte de contraintes peut alors être démontrée par réduction à un nombre fini de motifs binaires. Il faut appeler la méthode une adaptation de génération de contraintes, et expliquer sa contribution propre : coûts continus bornés, recours continu temporel, marge prescrite, parcimonie et protocole reproductible. Le simple ajout d'indices temporels ne démontre pas une nouvelle méthode de décomposition.

La nouveauté générale du projet initial est devenue intenable. L'article récent d'Engelhardt et al. traite déjà les explications faibles et fortes en optimisation entière et propose des algorithmes de génération de contraintes ; le détail des antériorités est conservé dans `article/literature_notes.md`. Une comparaison explicite avec cette formulation est nécessaire avant soumission.

## Erreurs bloquantes dans le manuscrit archivé

### 1. Une borne lagrangienne inférieure ne fournit pas la coupe annoncée

La proposition `prop:lagrangian_bound` impose `coût(foil) ≤ borne_lagrangienne`. L'optimalité ne requiert que `coût(foil) ≤ optimum_forward`, tandis que la borne lagrangienne peut être strictement plus petite. La proposition élimine donc des explications valides.

Contre-exemple exact : minimiser `x` sous `x ∈ {0,1}` et `x ≥ 1/2`. L'unique solution et le foil sont `x=1`, d'objectif 1. En relaxant `1/2-x ≤ 0`, la borne est

\[
L(\mu)=\min_{x\in\{0,1\}}\{x+\mu(1/2-x)\}
=\min\{\mu/2,1-\mu/2\},\quad \mu\ge0.
\]

Même sa meilleure valeur est `1/2`. La coupe proposée devient `1 ≤ 1/2`. Une borne inférieure peut servir à **certifier** une solution quand son coût coïncide avec cette borne ; l'imposer comme condition nécessaire est incorrect. Les solutions de sous-problèmes temporels relaxés ne sont pas nécessairement des trajectoires physiquement réalisables et ne doivent pas produire de coupes ordinaires avant reconstruction et validation.

### 2. Les trajectoires ne sont pas transportables entre capacités différentes

Une coupe n'est valide que si son compétiteur est réalisable pour les paramètres considérés. Considérer `min -x`, `x∈{0,1}`, `x≤b`, foil `x=0`. Le compétiteur `x=1` produit la coupe `0≤-1` pour `b=1`. Réutilisée pour `b=0`, elle élimine le foil, pourtant seule solution réalisable.

À l'inverse, comparer seulement aux trajectoires nominales omet les nouveaux compétiteurs après expansion. Avec `x∈{0,1,2}`, `x≤b`, coût `-x`, capacité nominale 0 et nouvelle capacité 2, le foil `x=1` bat la seule trajectoire nominale `x=0` mais perd contre `x=2`. Il ne constitue pas une explication faible. Un menu fini de capacités, résolu indépendamment scénario par scénario, répare ces deux erreurs. Ce menu ne doit pas être présenté comme une résolution exacte du problème de capacités continûment modifiables.

### 3. McCormick n'est pas une linéarisation exacte de deux variables continues

Pour `u,v∈[0,1]`, les enveloppes de McCormick autorisent `u=v=1/2,w=0`, alors que `uv=1/4`. Des bornes finies ne suffisent donc pas pour transformer le maître bilinéaire général en MILP exact. Le produit d'un coût borné et d'une variable **binaire** possède, lui, une formulation exacte. Il faut retirer la généralisation aux coûts des quantités continues.

### 4. La revendication générale NP-complète n'est pas établie

Le théorème `thm:np_complete_cost` mélange description implicite du convexe entier et description polynomiale explicitement disponible. Carathéodory ne donne pas gratuitement un certificat d'optimalité vérifiable pour un MILP quelconque.

Voici une obstruction directe : pour une formule SAT de clauses `C_j`, introduire les variables binaires d'affectation `z` et `t`, les contraintes `somme des littéraux de C_j ≥ t`, et minimiser `-t`. Le vecteur entièrement nul, avec `t=0`, est réalisable. Avec coûts non modifiables et foil égal à ce vecteur, l'explication existe exactement quand la formule est insatisfiable. Même ce sous-cas est donc coNP-difficile. Une appartenance générale à NP impliquerait NP=coNP.

L'annexe restreinte ne répare pas le théorème principal : elle modifie ses hypothèses. Son instance de Partition contient une contrainte de sac à dos dont elle ne fournit pas la description polynomiale du convexe entier. L'intégralité d'un polyèdre n'est pas synonyme de disponibilité d'une description polynomiale de l'enveloppe entière d'un MILP. La réduction Set Cover esquissée doit aussi être explicitement construite avant de pouvoir constituer une preuve.

La réduction Σ₂ décrite dans l'autre annexe semble, pour sa partie **difficulté**, exploiter correctement le budget saturé et la monotonie des littéraux d'affectation. Il ne faut pas la rejeter indistinctement. En revanche, l'appartenance annoncée pour le modèle mixte général suppose sans démonstration un témoin de taille polynomiale malgré les produits continus. Le design de remplacement n'a pas besoin d'une classification générale non établie. Les antériorités de 2025–2026 doivent de toute façon être discutées.

### 5. Une région de confiance ne certifie pas l'infaisabilité globale

Exemple : `min (2+δ)y`, `y∈{0,1}`, foil `y=1`, `δ∈[-3,0]`. Une explication faible existe dès `δ≤-2`. Le maître limité à `|δ|≤1` est infaisable. Retourner « aucune explication dans l'ensemble actionnable » est faux. Toute stabilisation doit finalement lever sa restriction avant de certifier l'infaisabilité ou une borne globale.

### 6. Les assertions empiriques et humaines ne sont pas des résultats

Les tableaux sont explicitement des placeholders. Ils ne justifient ni gain d'un ordre de grandeur, ni supériorité à un solveur bilevel, ni scores d'actionnabilité humains. Ces assertions doivent être retirées jusqu'à mesure effective. La parcimonie est une propriété mesurable du vecteur de perturbation ; son interprétabilité humaine requiert une évaluation humaine distincte.

L'expression « epsilon-relative » n'est pas définie dans le texte archivé. Une tolérance additive sur l'optimalité du problème modifié n'est pas automatiquement la notion de CE relative de la littérature. Les notions doivent être nommées et définies séparément.

## Formulation exacte recommandée

Fixer un scénario de capacité `s`. Soit

\[
X_s=\{(y,z): y\in\{0,1\}^m,\ A_sy+B_sz\le b_s\},\qquad
f_\delta(y,z)=(c+\delta)^\top y+d^\top z.
\]

`z` regroupe toutes les quantités et tous les états continus. Les équations de bilan restent dans `X_s`. Le vecteur `d`, les matrices et `b_s` ne dépendent pas de `δ`. Supposer que chaque motif réalisable a un recours de valeur finie et atteinte. Le foil `F` est une propriété des binaires, par exemple `y_j=a_j` pour `j∈J`. Définir

\[
Y_s=\{y:\exists z,(y,z)\in X_s\},\qquad
q_s(y)=\min\{d^\top z:(y,z)\in X_s\}.
\]

Alors `Y_s` est fini et `q_s(y)` est indépendant de `δ`. Tous les concurrents d'un même motif sont dominés par celui de recours minimal. Définir `v_F(δ)` comme le minimum de `(c+δ)'y+q_s(y)` sur `Y_s∩F`, `v_N(δ)` sur `Y_s\F`, et `v(δ)=min(v_F,v_N)`. Le minimum d'un ensemble vide est `+∞`.

| Régime | Condition exacte | Oracle de séparation |
|---|---|---|
| Faible | `v_F = v`, avec `v_F` fini | Tous les motifs |
| Epsilon-optimal additif | `v_F ≤ v+ε`, `ε≥0` fixé | Tous les motifs |
| Fort classique | `v_F < v_N`, avec `v_F` fini | Motifs hors foil |
| Fort avec marge | `v_F+γ ≤ v_N`, `γ>0` fixé | Motifs hors foil |

Une marge prescrite implique la propriété forte mais peut exclure des explications fortes valides dont la marge est plus petite. Elle ne doit pas être annoncée comme équivalente au fort classique pour tout `γ`. Grâce au nombre fini de motifs, chaque explication forte possède une marge positive, mais cette marge varie avec les paramètres.

### Coupes et produits exacts

Pour un témoin foil `(ŷ,ẑ)` et un compétiteur optimal pour son motif `y^k`, la coupe est

\[
f_\delta(\hat y,\hat z)\le(c+\delta)^\top y^k+q_s(y^k)+\varepsilon
\]

dans le régime epsilon, avec `ε=0` dans le régime faible. Dans le régime fort avec marge, utiliser seulement des compétiteurs hors foil et remplacer le membre droit par `(c+δ)'y^k+q_s(y^k)-γ`.

Pour `w_i=δ_i ŷ_i`, `L_i≤δ_i≤U_i`, les quatre inégalités exactes sont

\[
L_i\hat y_i\le w_i\le U_i\hat y_i,\quad
\delta_i-U_i(1-\hat y_i)\le w_i\le\delta_i-L_i(1-\hat y_i).
\]

Les indicateurs de support imposent `L_i u_i≤δ_i≤U_i u_i`, puis `u_i≤a_t` pour la période concernée. Il faut que l'absence de modification soit autorisée et que les bornes encadrent zéro. Sans pénalité strictement positive sur les indicateurs, un indicateur à 1 n'implique pas un changement non nul : rapporter aussi le support numérique effectif avec sa tolérance déclarée.

### Complément du foil

Pour un foil conjonctif `y_j=a_j`, `j∈J`, son complément exact est

\[
\sum_{j\in J:a_j=1}(1-y_j)+\sum_{j\in J:a_j=0}y_j\ge1.
\]

Comparer seulement à l'inversion de **tous** les bits du foil omettrait des nonfoils. Un foil vide a un complément vide ; tout optimum satisfait alors le foil. Si des foils portant sur les variables continues sont ajoutés, leur complément peut comporter des inégalités strictes et ne pas être fermé ; la formulation et la preuve ci-dessus doivent être revisitées.

### Preuve de terminaison et d'optimalité

À chaque itération non terminale, l'oracle exact fournit un motif qui viole une coupe absente. Un motif déjà ajouté avec sa valeur exacte `q_s(y)` ne peut plus être violant. Il y a donc au plus `|Y_s|` ajouts de motifs, ou `|Y_s\F|` pour la marge forte. Une implémentation ne générant que des coupes peut être appelée « génération de contraintes » ; elle n'a pas nécessairement de nouvelles colonnes.

Le maître est une relaxation de l'explication complète. Son optimum est une borne inférieure du coût d'explication. Lorsque la séparation ne trouve aucune violation, son témoin est réalisable pour toutes les contraintes et possède ce même coût : borne inférieure et supérieure coïncident. Si le maître global est infaisable, le problème complet l'est aussi.

**Point crucial epsilon :** `+ε` doit apparaître dans toutes les coupes du maître. Utiliser un maître faible exact puis accepter un résidu inférieur à `ε` ne démontre pas l'optimalité du coût d'explication parmi toutes les explications epsilon-optimales.

Cette preuve suppose des résolutions exactes au sens mathématique. Dans l'implémentation numérique, déclarer tolérances de faisabilité, d'intégralité et d'optimalité, distinguer optimum certifié aux tolérances, solution faisable et interruption. Une valeur incumbent de l'oracle est une borne supérieure de son minimum : elle peut prouver une violation, mais pas l'absence de violation. Pour certifier un témoin de coût `C`, une borne inférieure `L` de l'oracle suffit si `C≤L+ε`, ou `C+γ≤L` dans le régime fort. L'infaisabilité du complément doit être prouvée, et non déduite de l'absence d'incumbent.

### Existence et robustesse de la marge

La propriété forte sans marge peut avoir un infimum non atteint. Exemple : `min δy`, `y∈{0,1}`, foil `y=1`, coût d'explication `|δ|`, `δ∈[-1,1]`. La région forte est `δ<0`, son infimum est zéro, sans minimiseur. Fixer `γ>0` donne la région fermée `δ≤-γ`. Avec coûts bornés, nombre fini de motifs et de supports, le problème de marge prescrit possède un minimum dès qu'il est réalisable.

Un certificat simple de stabilité peut être ajouté sans prétendre à une nouvelle théorie générale. Si un témoin foil bat chaque nonfoil de marge au moins `γ`, une perturbation supplémentaire `e` des seuls coûts binaires change chaque différence d'objectif d'au plus `||e||∞ ||ŷ-y||₁≤m||e||∞`. Toute perturbation vérifiant `m||e||∞<γ` préserve donc la propriété forte. La borne plus fine est `Σ_i η_i|ŷ_i-y_i|` lorsque `|e_i|≤η_i`. Cette garantie ne couvre ni une modification de capacité ni un changement du coût du recours.

## Conditions expérimentales à vérifier avant soumission

1. Comparer CCG, une variante à plusieurs coupes et l'énumération complète des motifs sur les **mêmes** petites instances. Inclure le temps de calcul des recours et le temps de construction de tous les modèles dans l'énumération. Conserver un temps total de bout en bout, avec compilation Julia séparée.
2. Tester les trois régimes avec les mêmes fenêtres et foils ; inclure égalités, foils déjà optimaux, foils irréalisables, complément vide et explications inexistantes sous les bornes. Vérifier indépendamment les paramètres retournés en résolvant les modèles foil/global/nonfoil pertinents.
3. Pour chaque capacité, conserver séparément coupes, résultat et bornes. Le meilleur scénario connu est seulement un incumbent tant que des scénarios peuvent battre sa valeur. Déclarer le coût d'intervention et sa normalisation, et inclure le scénario nominal dans le menu.
4. Fixer le choix des fenêtres de données, des foils, des semences et des exclusions avant l'analyse. Conserver les échecs. Les fenêtres fortement chevauchantes d'une même série ne sont pas des répétitions indépendantes ; utiliser des résumés descriptifs ou un bootstrap par série/source.
5. Publier statuts et taux de résolution à chaque budget. Ne pas comparer seulement les temps des succès respectifs. Distinguer performance appariée sur succès communs, résultats censurés et temps total. Des pilotes courts ne justifient pas une affirmation de passage à l'échelle.
6. Distinguer séries d'activité observées et paramètres opérationnels construits. Des admissions ou passages réels ne sont pas des données de coûts, de personnel, de durées de séjour individuelles ou de programmation opératoire. Présenter le cas hospitalier comme banc d'essai stylisé alimenté par une série réelle tant qu'aucune calibration métier n'est faite.
7. Vérifier si la parcimonie réduit seulement le nombre de modifications ou améliore aussi leur lisibilité dans une étude utilisateur. Sans cette étude, employer « support temporel réduit », pas « interprétabilité humaine démontrée ».
8. Avant une revendication de nouvelle méthode, reproduire une baseline tirée de l'antériorité la plus proche ou expliciter les adaptations nécessaires. Une comparaison contre sa propre version sans accélération est une ablation, pas une validation de supériorité sur l'état de l'art.

## Décision de relecture

**Design restreint : recevable pour implémentation, sous les hypothèses explicites ci-dessus. Manuscrit original : non soumettable en l'état.** Les obstacles restants à une soumission ambitieuse sont la preuve d'une contribution qui dépasse l'adaptation, l'ampleur et la représentativité des expériences, la comparaison bibliographique directe et la validation du lien entre données observées et modèle opérationnel. La correction mathématique et la reproductibilité sont nécessaires, mais ne suffisent pas à garantir l'acceptation dans une revue donnée.
