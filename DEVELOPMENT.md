# Maintenance et reprise du site

Ce document est la mémoire technique du site <https://dreuzy.github.io>. Le dépôt doit suffire à reprendre le site sans dépendre d’un ancien échange.

## 1. Architecture

Le site est statique et servi directement par GitHub Pages depuis la branche `main`.

- les pages françaises sont à la racine ;
- leurs équivalents anglais sont dans `en/` ;
- `mirror-map.json` définit les couples de pages ;
- `site-config.json` centralise la navigation, le pied de page, les coordonnées, la section active et les quelques valeurs partagées du CV ;
- `styles.css` est la feuille de style commune ;
- `data/bibliography.json` est la source éditable de la bibliographie ;
- `assets/figure-data/manifest.json` décrit toutes les figures reconstructibles à partir de fragments ;
- `scripts/build_visual_assets.py` reconstruit le portrait local, les diagrammes directs et les cartes sociales ;
- `scripts/build_curated_content.py` maintient les blocs éditoriaux structurés et bilingues des pages les plus évolutives ;
- `requirements.txt` déclare toutes les dépendances Python ;
- le `Makefile` fournit l’interface de maintenance.

Il n’existe ni framework client ni chargement obligatoire de données au démarrage. La bibliographie et les figures sont matérialisées dans les fichiers publiés.

## 2. Installation et commandes

Utiliser Python 3.12 ou plus récent :

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

Commandes principales :

```bash
make build       # reconstruit toutes les sorties
make check       # contrôle sans modifier les sorties
make all         # build, puis check
make serve       # prévisualisation sur http://localhost:8000
```

Sous Windows PowerShell, activer l’environnement avec `.venv\Scripts\Activate.ps1`, puis utiliser `python` et `make` si GNU Make est installé. À défaut, les commandes du `Makefile` peuvent être exécutées une par une.

Une construction reproductible doit respecter :

```bash
make all
make all
git diff --exit-code
```

La seconde exécution ne doit produire aucune différence supplémentaire.

## 3. Pages bilingues

`mirror-map.json` contient 24 couples de pages. Les couples `a-propos` et `research-figures` sont des redirections techniques ; les anciennes adresses de la galerie mènent désormais à la section « Images et médiation ». Les 22 autres couples sont indexables.

### Modifier une page

1. modifier la page française et sa page anglaise ; pour l’accueil ou un bloc pris en charge par `build_curated_content.py`, modifier d’abord ce générateur ;
2. conserver la même structure générale, les mêmes figures et des liens croisés réciproques ;
3. lancer `make layout` si la navigation, les coordonnées ou les métadonnées d’URL ont changé ;
4. lancer `make check`.

### Ajouter une page

1. créer les versions FR et EN ;
2. ajouter le couple à `mirror-map.json` ;
3. ajouter son rattachement à `page_sections` dans `site-config.json` ;
4. ajouter un seul `h1`, `main#main-content`, une description, les métadonnées sociales et les dimensions intrinsèques de chaque image ;
5. lancer `make layout sitemap`, puis `make check`.

`scripts/sync_shared_layout.py` génère :

- le lien d’évitement ;
- la navigation et son état actif ;
- le sélecteur FR/EN ;
- le pied de page ;
- les canonical, hreflang et `og:url`.
- les images Open Graph et Twitter par famille de pages ;
- les profils externes du balisage `Person` de l’accueil.

Le mode `--check` échoue si un bloc commun a été modifié à la main ou n’a pas été régénéré.

## 4. Bibliographie

### Source

`data/bibliography.json` remplace les anciens payloads gzip/Base64. Le fichier contient :

- les sections ;
- leurs groupes ;
- l’ordre des listes ;
- une entrée stable `id` pour chaque référence ;
- le HTML localisé `fr` et `en`.

Une entrée ressemble à :

```json
{
  "id": "articles-...-115",
  "html": {
    "fr": "Auteurs (2026), <a href=\"...\">Titre</a>...",
    "en": "Authors (2026), <a href=\"...\">Title</a>..."
  }
}
```

### Ajouter ou corriger une référence

1. modifier `data/bibliography.json` ;
2. conserver un identifiant unique et stable ;
3. renseigner les deux variantes linguistiques ;
4. pour un nouvel article, l’insérer à la bonne place dans le groupe `articles-publies` ;
5. si le nombre total change volontairement, mettre à jour `bibliography_reference_counts` et `cv.publication_count` dans `site-config.json` ;
6. lancer `make bibliography`, puis `make check`.

Le générateur produit :

- `bibliographie.html` ;
- `en/bibliography.html` ;
- `publications-au-fil-du-temps.svg` ;
- `en/publications-au-fil-du-temps.svg` ;
- `publications-au-fil-du-temps-data.json`.

Il alimente également le bloc « Dernières publications » des pages de sélection. `bibliography-filter.js` fournit la recherche par mots-clés, type et année sans masquer le contenu lorsque JavaScript est désactivé.

`bibliography-hal.js` reste un enrichissement facultatif. Une indisponibilité de HAL ne retire aucun contenu bibliographique.

### Doublons

`scripts/check_site_quality.py` détecte :

- les identifiants en double ;
- les DOI en double parmi les articles publiés ;
- les titres exactement identiques ;
- les titres fortement similaires ;
- les titres assez similaires associés à des listes d’auteurs presque identiques.

Les paires proches mais réellement distinctes sont documentées dans `data/bibliography-duplicate-allowlist.json` avec une justification. Ne jamais ajouter une exception uniquement pour faire passer le contrôle : comparer d’abord titre, auteurs, année, revue et DOI.

## 5. Figures

### Assets directs et générés

Les images ordinaires sont référencées directement dans les pages. `scripts/build_visual_assets.py` reconstruit le portrait local à partir de sa source encodée, le diagramme FutureFlow, la copie normalisée du visuel HydroModPy et les cartes sociales de 1200 × 630 pixels. OneWater utilise `assets/figures/onewater.svg`.

`scripts/check_media_assets.py` décode entièrement chaque JPEG, PNG et WebP et parse chaque SVG. Une image tronquée ou un SVG XML invalide font donc échouer `make check` avant publication.

Chaque balise `img` doit avoir :

- un texte alternatif utile ;
- une largeur et une hauteur intrinsèques ;
- un chemin qui existe dans le dépôt.

### Figures reconstructibles

`assets/figure-data/manifest.json` contient, pour chaque figure :

- le nom commun des fragments ;
- le nombre de fragments ;
- le chemin de sortie ;
- la taille attendue ;
- le SHA-256 attendu.

`scripts/materialize_figure_assets.py` concatène les fragments Base64, vérifie qu’ils produisent un WebP, puis vérifie taille et empreinte avant écriture.

```bash
make figures
python scripts/materialize_figure_assets.py --check
python scripts/materialize_figure_assets.py --name pyages-final-v2
```

Le navigateur ne charge jamais les fragments. Les attributs historiques `data-b64-*` et `figure-loader.js` sont interdits par le contrôle qualité.

### PyAges

- `assets/pyages-software-figure.webp` illustre les pages Logiciels / Software ;
- `assets/pyages-groundwater-age-v2.webp` illustre les pages PyAges ;
- les neuf fragments `pyages-final-v2.part-*.txt` sont la source vérifiée de la seconde image.

Le workflow `build-pyages-image.yml` appelle le même script et le même manifeste que la maintenance locale : il n’existe plus de taille ou d’empreinte dupliquée dans le YAML.

## 6. CV PDF

`scripts/build_cv_pdf.py` génère le PDF indiqué par `cv.pdf` dans `site-config.json`. La date courte, la date complète et le nombre d’articles sont également centralisés dans ce bloc.

```bash
make cv
python scripts/build_cv_pdf.py --check
```

Le mode invariant de ReportLab et l’écriture conditionnelle rendent le PDF reproductible. Après une évolution annuelle importante, mettre à jour ensemble :

- le contenu du script ;
- le nom de fichier si l’année change ;
- le bloc `cv` de `site-config.json` ;
- les liens de téléchargement des pages CV FR/EN.

## 7. Sitemap, SEO et accessibilité

`scripts/build_sitemap.py` dérive le sitemap directement de `mirror-map.json`. Les redirections et la page 404 n’y figurent pas.

Chaque page de contenu doit conserver :

- un titre non vide et une description substantielle ;
- un canonical unique ;
- les hreflang `fr`, `en` et `x-default` ;
- les métadonnées Open Graph et Twitter ;
- exactement un `h1` ;
- `main#main-content` et le lien d’évitement ;
- des identifiants HTML uniques ;
- des images accessibles et dimensionnées.

`scripts/check_local_links.py` contrôle les fichiers locaux et, désormais, les fragments d’URL comme `page.html#section`.

Les redirections et `404.html` doivent rester en `noindex,follow`.

## 8. Workflows GitHub Actions

Quatre workflows permanents sont conservés :

| Workflow | Rôle |
| --- | --- |
| `check-bilingual-mirror.yml` | Installe les dépendances déclarées et lance `make check` à chaque push ou pull request. |
| `build-pyages-image.yml` | Reconstruit l’image PyAges depuis le manifeste et committe uniquement une sortie réellement modifiée. |
| `update-publications-over-time.yml` | Reconstruit la bibliographie et les graphiques après une modification de la source, ainsi que le 1er janvier. |
| `verify-pyages-live.yml` | Vérifie après publication que l’image Logiciels est réellement disponible sur le site. |

Les générateurs sont déterministes : un workflow relancé sans modification de source ne doit plus créer de commit parasite.

## 9. Contrôles exécutés par `make check`

Dans l’ordre :

1. reproductibilité des visuels et décodage de tous les médias ;
2. intégrité des figures fragmentées et synchronisation du contenu structuré ;
3. synchronisation des pages de bibliographie et des dernières publications ;
4. synchronisation des graphiques et données temporelles ;
5. synchronisation du CV PDF ;
6. synchronisation des blocs partagés et des métadonnées sociales ;
7. synchronisation du sitemap ;
8. parité structurelle FR/EN ;
9. liens, ressources et ancres internes ;
10. SEO, accessibilité de base, inventaire des pages, bibliographie et doublons.

Un échec indique le fichier concerné et, lorsque c’est pertinent, la commande de reconstruction.

## 10. Contrôle après publication

Après une modification importante :

1. attendre la fin du déploiement GitHub Pages ;
2. vérifier la page d’accueil et les pages modifiées en FR et EN ;
3. ouvrir au moins un PDF et les figures modifiées ;
4. vérifier le sitemap publié ;
5. vérifier que les quatre workflows sont verts.

Les codes `403`, `429` ou `999` renvoyés par certains sites externes à des robots ne suffisent pas à conclure qu’un lien est mort. Les liens DOI, éditeurs, HAL, OSERen, Google Scholar ou LinkedIn doivent être vérifiés avec discernement.

## 11. État de référence — septembre 2026

- 49 fichiers HTML, dont 44 pages indexables, quatre redirections et une page 404 ;
- 24 couples FR/EN ;
- 114 articles publiés ;
- 256 abstracts de colloques ;
- 14 actes de colloques ;
- 10 figures WebP reconstructibles, dont PyAges ;
- trois dossiers de contrats et deux pages logicielles bilingues ;
- un CV PDF A4 de quatre pages ;
- quatre workflows permanents.

Les anciens payloads opaques de bibliographie, les fragments FutureFlow/OneWater inutilisés et le script ponctuel de migration de l’audit ont été retirés. Ils restent récupérables dans l’historique Git si une enquête rétrospective est nécessaire.

## 12. Reprise après une interruption

1. lire `README.md` puis ce document ;
2. installer les dépendances ;
3. exécuter `make check` avant toute modification ;
4. lire `mirror-map.json`, `site-config.json` et la source de données concernée ;
5. effectuer la modification dans les deux langues ;
6. exécuter `make all` ;
7. examiner le diff, puis publier ;
8. contrôler le site et les workflows en ligne.
