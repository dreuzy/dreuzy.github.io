# Maintenance et reprise du site

Ce document est la mémoire technique du site personnel de Jean-Raynald de Dreuzy (`https://dreuzy.github.io/`). Il doit permettre de reprendre le site après plusieurs mois, par une autre personne ou par un assistant, sans dépendre d’un ancien fil de discussion.

Le site est volontairement statique, sans framework ni étape de compilation générale. La branche publiée est `main` et GitHub Pages sert directement les fichiers du dépôt.

## 1. Principes à conserver

1. La version française est à la racine du dépôt ; la version anglaise correspondante est dans `en/`.
2. Toute modification de contenu ou de structure d’une page FR doit être répercutée sur sa page EN dans la même opération logique.
3. `mirror-map.json` est la référence des couples de pages FR/EN.
4. Avant de considérer une modification terminée, exécuter :

   ```bash
   python scripts/check_bilingual_mirror.py
   python scripts/check_local_links.py
   ```

5. Ne pas supprimer un asset ou une famille `assets/figure-data/*.part-XX.txt` sans vérifier qu’elle n’est plus utilisée par les pages, les scripts ou les workflows.
6. Les workflows `one-shot-*` sont des outils temporaires de maintenance : s’ils sont créés pour une intervention, ils doivent être supprimés après validation. En régime normal, seuls les quatre workflows permanents documentés plus bas doivent rester.

## 2. Organisation du dépôt

Principaux éléments :

- `*.html` : pages françaises à la racine.
- `en/*.html` : pages anglaises en miroir.
- `styles.css` : feuille de style commune.
- `assets/figures/` : images et schémas utilisés directement par les pages.
- `assets/figures/embedded/` : WebP matérialisés à partir des anciennes familles Base64.
- `assets/figure-data/` : fragments texte conservés comme sources de reconstruction, jamais chargés par le navigateur.
- `assets/` : autres images visibles du site, notamment PyAges et les maquettes de la rubrique Science & société.
- `mirror-map.json` : correspondance officielle FR/EN.
- `scripts/check_bilingual_mirror.py` : contrôle de la cohérence du miroir bilingue.
- `scripts/check_local_links.py` : contrôle des liens et ressources locales.
- `scripts/materialize_figure_assets.py` : reconstruction des WebP directs depuis les fragments Base64 historiques.
- `scripts/build_static_bibliography.py` : reconstruction de la bibliographie HTML statique FR/EN à partir des payloads.
- `scripts/build_publications_over_time.py` : génération des graphiques « publications au fil du temps ».
- `scripts/build_cv_pdf.py` : génération du CV PDF téléchargeable.
- `bibliographie-payload-01.txt` à `bibliographie-payload-05.txt` : source compressée/encodée de la bibliographie complète.
- `bibliography-hal.js` : enrichissement facultatif des entrées bibliographiques avec les notices HAL.
- `sitemap.xml`, `robots.txt`, `.nojekyll` : fichiers de publication/SEO.
- `.github/workflows/` : automatisations permanentes.

## 3. Structure bilingue

`mirror-map.json` décrit actuellement 23 couples de pages. Le français est la langue par défaut. La navigation principale comporte huit entrées : accueil, recherche, projets & contrats, équipe, publications, logiciels, science & société et CV.

Les deux pages techniques suivantes sont des redirections vers le CV :

- `a-propos.html`
- `en/about.html`

Elles doivent rester légères et ne sont pas des pages de contenu indépendantes.

### Modification d’une page

Lorsqu’une page est modifiée :

1. modifier la page FR et sa page EN ;
2. conserver le même ordre général des blocs et des figures ;
3. vérifier les liens de langue réciproques ;
4. conserver les balises `canonical` et `hreflang` cohérentes ;
5. exécuter les deux scripts de contrôle.

Si une nouvelle page est ajoutée, l’ajouter également à `mirror-map.json`, créer son équivalent dans l’autre langue et décider explicitement si elle doit figurer ou non dans `sitemap.xml`.

## 4. Figures et images

Il existe deux mécanismes différents.

### 4.1 Images normales

Les fichiers comme :

- `assets/figures/fractured-media-channeling.webp`
- `assets/figures/eau-territoire.webp`
- `assets/figures/futureflow-framework.webp`
- `assets/figures/hydromodpy-approved.webp`
- `assets/figures/onewater.svg`
- `assets/maquette-nappes.jpg`
- `assets/maquette-fractures.jpg`

sont référencés directement par `src=` dans les pages.

Ne pas conserver d’anciennes variantes « au cas où » dans `assets/` : lors du nettoyage de septembre 2026, les fichiers non référencés ont été supprimés. Git conserve l’historique si une ancienne version doit être récupérée.

### 4.2 Figures issues de `figure-data`

Certaines figures ont pour source des fragments texte Base64 :

`assets/figure-data/<nom>.part-00.txt`, `part-01.txt`, etc.

Le script `scripts/materialize_figure_assets.py` concatène et décode ces fragments en fichiers WebP sous `assets/figures/embedded/`, puis remplace dans les pages les anciens attributs `data-b64-*` par un `src` direct. Les pages publiées ne dépendent donc plus de JavaScript ni de dizaines de requêtes texte pour afficher ces figures.

Pour reconstruire les WebP après une modification volontaire des sources :

- ne jamais supprimer un fragment isolé d’une série active ;
- exécuter `python scripts/materialize_figure_assets.py` ;
- contrôler les images produites, puis les liens locaux et le miroir bilingue ;
- conserver les pages avec des références `src=` directes : le chargeur JavaScript historique ne doit pas être réintroduit.

## 5. Cas particulier PyAges

Deux images PyAges ont des fonctions différentes :

- `assets/pyages-software-figure.webp` est utilisée sur les pages Logiciels / Software.
- `assets/pyages-groundwater-age-v2.webp` est utilisée sur les pages PyAges.

### Reconstruction de l’image groundwater-age

Les neuf fichiers :

`assets/figure-data/pyages-final-v2.part-00.txt` à `part-08.txt`

sont les sources de reconstruction de `assets/pyages-groundwater-age-v2.webp`.

Le workflow `.github/workflows/build-pyages-image.yml` :

1. concatène et décode les neuf fragments ;
2. reconstruit le WebP ;
3. vérifie sa taille attendue et son SHA-256 ;
4. committe l’image seulement si elle a changé.

Ne pas modifier manuellement l’image reconstruite sans comprendre ce mécanisme : le workflow considère les neuf fragments comme la source vérifiée.

### Vérification de l’image Logiciels

`.github/workflows/verify-pyages-live.yml` vérifie après déploiement que `assets/pyages-software-figure.webp` est bien une image WebP substantielle et que les pages FR/EN la référencent correctement.

## 6. Bibliographie complète

La page `bibliographie.html` et son équivalent anglais contiennent la bibliographie complète directement dans le HTML. Le contenu principal reste donc lisible, indexable et exploitable sans JavaScript.

### Source principale

Les cinq fichiers `bibliographie-payload-01.txt` à `bibliographie-payload-05.txt` contiennent ensemble un document HTML compressé avec gzip puis encodé en Base64.

`scripts/build_static_bibliography.py` :

1. charge, concatène et décompresse les cinq fragments ;
2. applique les normalisations et ajustements éditoriaux FR/EN ;
3. fusionne les deux anciennes rubriques de proceedings sous une seule rubrique « Actes de colloques » ;
4. ajoute les métadonnées locales vérifiées des publications récentes ;
5. distingue les DOI d’articles réutilisés comme liens associés à des abstracts ;
6. insère le résultat statique dans `bibliographie.html` et `en/bibliography.html`.

Les payloads ne sont donc pas de simples fichiers texte à éditer ligne par ligne. Ne pas les modifier à la main sans reconstruire correctement le contenu gzip/Base64.

### Ajustements et enrichissements

Les métadonnées de RIVAGES Normands 2100 et d’HydroModPy sont conservées localement par le générateur : une panne de Crossref ne peut donc plus rétablir un ancien statut « accepté ».

`bibliography-hal.js` interroge l’API HAL et ajoute, lorsque c’est possible, un lien `[HAL]` aux entrées correspondantes. Cette étape est volontairement facultative : si HAL est indisponible, la bibliographie doit rester utilisable.

Après toute mise à jour des payloads ou des ajustements explicites du générateur, exécuter `python scripts/build_static_bibliography.py`, puis les deux contrôles du site. Vérifier en particulier les DOI, les titres proches et les listes d’auteurs proches afin d’éviter les faux doublons.

## 7. Publications au fil du temps

`scripts/build_publications_over_time.py` lit les cinq payloads de bibliographie et génère :

- `publications-au-fil-du-temps.svg`
- `en/publications-au-fil-du-temps.svg`
- `publications-au-fil-du-temps-data.json`

Le workflow `.github/workflows/update-publications-over-time.yml` se déclenche :

- manuellement ;
- lors d’une modification des payloads ou du script ;
- une fois par an, le 1er janvier.

Il installe `matplotlib` et `beautifulsoup4`, reconstruit les graphiques et les données, valide les liens locaux puis committe les sorties uniquement si elles ont changé.

## 8. SEO et indexation

Pour chaque vraie page de contenu, conserver :

- un `<title>` non vide ;
- une meta description ;
- un canonical unique ;
- un seul `<h1>` ;
- les trois `hreflang` : `fr`, `en`, `x-default` ;
- des `alt` non vides pour les images ;
- un `og:url` cohérent avec le canonical lorsqu’il est présent.

La galerie scientifique FR/EN contient désormais un contenu éditorial original, possède ses métadonnées sociales et est indexée comme les autres pages de contenu. Seules les pages techniques de redirection et `404.html` ne doivent pas être indexées.

### Sitemap

À l’état de référence du 20 septembre 2026, `sitemap.xml` contient exactement 44 URL, soit toutes les pages de contenu indexables et seulement celles-ci.

`robots.txt` doit contenir :

```text
Sitemap: https://dreuzy.github.io/sitemap.xml
```

## 9. Workflows GitHub Actions permanents

En régime normal, `.github/workflows/` doit contenir exactement ces quatre fichiers :

| Workflow | Rôle |
| --- | --- |
| `check-bilingual-mirror.yml` | Vérifie le miroir FR/EN et les liens locaux. Sur un push `main`, attend 120 s afin que des modifications FR/EN rapprochées puissent arriver avant le contrôle. |
| `build-pyages-image.yml` | Reconstruit et vérifie l’image PyAges à partir des neuf fragments source. |
| `verify-pyages-live.yml` | Vérifie sur le site publié l’image PyAges de la page Logiciels et ses références FR/EN. |
| `update-publications-over-time.yml` | Régénère les figures et données « publications au fil du temps ». |

Les workflows temporaires `one-shot-*` ne doivent pas rester dans le dépôt après une opération de maintenance.

## 10. Checklist avant de terminer une modification

### Contrôle local/source

```bash
python scripts/check_bilingual_mirror.py
python scripts/check_local_links.py
```

Puis vérifier selon la nature du changement :

- parité FR/EN ;
- canonical / hreflang ;
- `sitemap.xml` si une page a été ajoutée, retirée ou passée en `noindex` ;
- intégrité des fragments `figure-data` si une figure matérialisée est reconstruite ;
- payloads et scripts de bibliographie si la bibliographie change ;
- absence d’asset devenu orphelin si une image est remplacée.

### Après publication

Pour une modification importante, contrôler au minimum :

- que les pages modifiées répondent en HTTP 200 ;
- que les assets modifiés sont effectivement publiés ;
- que les figures matérialisées répondent en HTTP 200 ;
- que le sitemap publié correspond au fichier du dépôt.

GitHub Pages peut avoir un court délai de propagation après un push.

## 11. Liens externes

Un contrôle automatique des liens externes est utile, mais ses résultats doivent être interprétés avec prudence.

Des sites comme DOI/Crossref, LinkedIn, Google Scholar, OSERen, certains éditeurs scientifiques ou ResearchGate peuvent renvoyer `403`, `429` ou `999` à un robot tout en fonctionnant normalement dans un navigateur.

Ne jamais supprimer ou remplacer un lien externe uniquement parce qu’un test automatisé reçoit un refus anti-bot. Vérifier manuellement ou par une autre source lorsqu’un lien semble réellement mort.

## 12. État de référence après l’audit du 20 septembre 2026

Cet état sert de point de comparaison, pas d’invariant éternel : les nombres pourront légitimement évoluer si le site s’enrichit.

- 47 fichiers HTML au total, dont `404.html`.
- 23 couples de pages décrits dans `mirror-map.json`.
- 44 pages indexables dans `sitemap.xml`.
- 2 pages de redirection et 1 page d’erreur en `noindex,follow`.
- Bibliographie complète statique : 114 articles publiés, 10 abstracts comportant un lien explicitement qualifié d’« article associé ».
- 3 dossiers de contrats bilingues : FutureFlow ; RIVAGES → ARCHANGE ; EAUX 2050 / RIVIÈRES 2070 / CYDRE.
- Toutes les images HTML ont des dimensions intrinsèques déclarées.
- Les grandes images PNG de contenu ont été converties en WebP.
- CV PDF A4 de 4 pages disponible sous `assets/cv/`.
- 9 WebP sous `assets/figures/embedded/`, matérialisés depuis leurs familles `assets/figure-data` et référencés directement par le HTML.
- 2 autres anciennes familles Base64 remplacées par des assets directs existants (FutureFlow et OneWater), après retrait de deux familles corrompues.
- 9 fragments source PyAges supplémentaires utilisés pour reconstruire l’image WebP.
- 4 workflows GitHub Actions permanents.

## 13. Reprise après une longue interruption

Pour reprendre le site après plusieurs mois :

1. lire `README.md`, puis ce document ;
2. regarder les derniers commits de `main` pour voir si l’état de référence a évolué ;
3. lire `mirror-map.json` avant d’ajouter ou de renommer une page ;
4. exécuter les deux scripts de contrôle avant toute modification importante ;
5. vérifier les quatre workflows permanents ;
6. effectuer les modifications par petites étapes et revalider après chaque étape ;
7. pour une intervention lourde, faire un audit du dépôt puis un contrôle du site publié.

L’ancien historique de conversation peut être utile pour comprendre des choix éditoriaux, mais il ne doit pas être nécessaire à la maintenance technique : ce dépôt et ce document doivent suffire à la reprise.
