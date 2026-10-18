# Données et provenance

`raw/` contient l'archive **UCI Online Retail** (22.6 MB) et les 12 CSV mensuels **NHS England A&E 2024–25**. `processed/` contient les panneaux agrégés utilisés par Julia. `metadata/` contient URLs, sommes SHA-256, licences, filtrage et en-têtes sources.

Sources : [UCI](https://archive.ics.uci.edu/dataset/352/online+retail), DOI [10.24432/C5BW33](https://doi.org/10.24432/C5BW33), Daqing Chen (2015), **CC BY 4.0** ; [NHS England](https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-2024-25/), **Open Government Licence**, [conditions](https://www.england.nhs.uk/terms-and-conditions-2/).

Attribution : Contains NHS England information licensed under the Open Government Licence v3.0. Utilisation de données UCI attribuées à Daqing Chen ; les agrégations et filtrages de ce projet sont des modifications.

Les données dérivées ne contiennent aucun identifiant de client. L'archive UCI source reste inchangée et inclut les champs d'origine. Les données hospitalières sont agrégées par organisation et mois. Les coûts, capacités, délais/persistances et foils sont des hypothèses de benchmark, **pas des observations téléchargées**.

La normalisation retail utilise les 13 semaines complètes du 3 janvier au 3 avril 2011 ; le classement des produits utilise les ventes de janvier à mars. Les fenêtres d'expérience commencent au plus tôt le 4 avril. Pour NHS, avril est la calibration et les expériences commencent en mai. Aucune imputation de mois manquant n'est réalisée : seuls les providers complets sont retenus.

La page HTML NHS vide issue d'une première tentative a été écartée ; les données effectives proviennent des URL CSV officielles vérifiées. Pour une acquisition identique, conserver le manifeste et comparer les empreintes : les sources publiques peuvent publier de nouvelles révisions sous la même URL.
