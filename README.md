# Jean-Raynald de Dreuzy — site académique

Site personnel : recherche, projets, équipe, publications et parcours.

Le site est volontairement statique et léger afin de rester simple à maintenir. Les pages HTML et le fichier `styles.css` peuvent être modifiés directement ; les schémas sont dans `assets/figures/`.

## Structure bilingue en miroir

La version française reste à la racine du site et la version anglaise dans le répertoire `en/`. Chaque page française possède un équivalent anglais direct, avec la même structure, le même ordre de navigation et les mêmes figures.

Les correspondances officielles sont définies dans `mirror-map.json`. Le script `scripts/check_bilingual_mirror.py` vérifie automatiquement :

- l’existence de chaque paire de pages FR/EN ;
- la réciprocité des liens de langue ;
- l’ordre identique de la navigation ;
- la parité des blocs de mise en page ;
- l’identité des figures entre les deux langues.

La vérification est exécutée par GitHub Actions à chaque modification grâce à `.github/workflows/check-bilingual-mirror.yml`.

Lors d'une modification d'une page, mettre à jour sa page miroir dans le même commit. Avant de pousser, vérifier localement avec `python scripts/check_bilingual_mirror.py` et `python scripts/check_local_links.py`.

Sur `main`, le workflow attend deux minutes avant de vérifier les pages. Un nouveau push pendant ce délai annule le contrôle précédent : les modifications FR/EN publiées en deux commits rapprochés ne déclenchent plus de fausse alerte. Le dernier état est toujours vérifié et un écart persistant reste une erreur. Les contrôles des pull requests et les lancements manuels restent immédiats.

Site public : https://dreuzy.github.io
