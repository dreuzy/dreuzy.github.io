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

Site public : https://dreuzy.github.io
