# Jean-Raynald de Dreuzy — site académique

Site personnel : recherche, projets, équipe, publications et parcours.

Site public : https://dreuzy.github.io

Le site est volontairement statique et léger afin de rester simple à maintenir. La branche publiée est `main` ; les pages HTML, `styles.css`, les assets et les scripts du dépôt sont servis par GitHub Pages.

## Avant toute reprise ou modification

Lire d’abord **[`DEVELOPMENT.md`](DEVELOPMENT.md)**. Ce document décrit l’architecture complète du site, les conventions FR/EN, les figures dynamiques, PyAges, la bibliographie, le SEO, les workflows GitHub Actions, les contrôles à effectuer et l’état de référence du dépôt.

Le site doit pouvoir être repris à partir du dépôt seul, sans dépendre d’un ancien fil de discussion.

## Structure bilingue en miroir

La version française est à la racine du site et la version anglaise dans `en/`. Chaque page française possède un équivalent anglais direct.

Les correspondances officielles sont définies dans `mirror-map.json`. Le script `scripts/check_bilingual_mirror.py` vérifie notamment l’existence des paires FR/EN, les liens de langue, la navigation et la cohérence des blocs et figures.

Lors d’une modification d’une page, mettre à jour sa page miroir dans la même opération logique.

## Contrôles de base

Avant de considérer une modification terminée :

```bash
python scripts/check_bilingual_mirror.py
python scripts/check_local_links.py
```

Le workflow `.github/workflows/check-bilingual-mirror.yml` exécute également ces contrôles sur GitHub Actions. Sur les pushes vers `main`, il attend deux minutes afin d’éviter les faux écarts lorsqu’une paire FR/EN est mise à jour en plusieurs commits rapprochés.

Pour les opérations touchant aux figures, à PyAges, à la bibliographie, au sitemap ou aux workflows, suivre les procédures détaillées dans `DEVELOPMENT.md`.
