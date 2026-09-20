# Jean-Raynald de Dreuzy — site académique

Site public : <https://dreuzy.github.io>

Le site est statique, bilingue et publié directement depuis la branche `main` par GitHub Pages. Les contenus restent lisibles sans JavaScript ; les scripts du dépôt servent uniquement à reconstruire et contrôler les fichiers publiés.

## Démarrage rapide

Python 3.12 ou plus récent est recommandé.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
make all
```

La commande à lancer avant chaque publication est :

```bash
make check
```

Elle contrôle les fichiers générés, le miroir FR/EN, les liens et ancres internes, le SEO, l’accessibilité de base, le sitemap, les figures, les comptes bibliographiques et les doublons exacts ou probables.

Pour prévisualiser localement :

```bash
make serve
```

Puis ouvrir <http://localhost:8000>.

## Sources à modifier

| Besoin | Source de référence | Reconstruction |
| --- | --- | --- |
| Contenu d’une page | page HTML FR et page HTML EN | aucune |
| Navigation, pied de page, coordonnées | `site-config.json` | `make layout` |
| Couple de pages FR/EN | `mirror-map.json` | `make layout sitemap` |
| Bibliographie complète | `data/bibliography.json` | `make bibliography` |
| Exceptions de titres proches | `data/bibliography-duplicate-allowlist.json` | aucune, puis `make check` |
| Figures fragmentées | fragments et `assets/figure-data/manifest.json` | `make figures` |
| CV PDF | `scripts/build_cv_pdf.py` et bloc `cv` de `site-config.json` | `make cv` |
| Styles | `styles.css` | aucune |

Les pages `bibliographie.html`, `en/bibliography.html`, les deux SVG de l’historique des publications, leur JSON de données, le PDF du CV, le sitemap et les WebP déclarés dans le manifeste sont des sorties générées. Ne pas les éditer sans modifier également leur source.

## Structure bilingue

Le français est à la racine et l’anglais dans `en/`. Les 23 couples officiels sont décrits dans `mirror-map.json`. Toute modification éditoriale doit être faite dans les deux langues au cours de la même opération.

Les blocs communs sont générés par `scripts/sync_shared_layout.py`. Les titres et descriptions propres à chaque page restent dans son `<head>` ; leurs canonical, hreflang et `og:url` sont synchronisés depuis le manifeste.

## Documentation complète

Lire [`DEVELOPMENT.md`](DEVELOPMENT.md) avant une modification structurelle. Il décrit les procédures d’ajout d’une page, d’une publication, d’une figure ou d’un nouveau PDF ainsi que les workflows GitHub Actions et les invariants contrôlés.
