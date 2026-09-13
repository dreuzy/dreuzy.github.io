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
- `figure-loader.js` et `en/figure-loader.js` : reconstruction côté navigateur des figures stockées sous forme de fragments Base64.
- `assets/figures/` : images et schémas utilisés directement par les pages.
- `assets/figure-data/` : fragments texte de certaines figures reconstruites dynamiquement.
- `assets/` : autres images visibles du site, notamment PyAges et les maquettes de la rubrique Science & société.
- `mirror-map.json` : correspondance officielle FR/EN.
- `scripts/check_bilingual_mirror.py` : contrôle de la cohérence du miroir bilingue.
- `scripts/check_local_links.py` : contrôle des liens et ressources locales.
- `scripts/build_publications_over_time.py` : génération des graphiques « publications au fil du temps ».
- `bibliographie-payload-01.txt` à `bibliographie-payload-05.txt` : source compressée/encodée de la bibliographie complète.
- `bibliography-loader.js`, `bibliography-updates.js`, `bibliography-hal.js` : chargement et enrichissement de la bibliographie.
- `sitemap.xml`, `robots.txt`, `.nojekyll` : fichiers de publication/SEO.
- `.github/workflows/` : automatisations permanentes.

## 3. Structure bilingue

`mirror-map.json` décrit actuellement 20 couples de pages. Le français est la langue par défaut. La navigation principale comporte huit entrées : accueil, recherche, projets, équipe, publications, logiciels, science & société et CV.

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

- `assets/figures/fractured-media-channeling.png`
- `assets/figures/eau-territoire.png`
- `assets/figures/futureflow-framework.webp`
- `assets/figures/hydromodpy-approved.webp`
- `assets/figures/onewater.svg`
- `assets/maquette-nappes.jpg`
- `assets/maquette-fractures.jpg`

sont référencés directement par `src=` dans les pages.

Ne pas conserver d’anciennes variantes « au cas où » dans `assets/` : lors du nettoyage de septembre 2026, les fichiers non référencés ont été supprimés. Git conserve l’historique si une ancienne version doit être récupérée.

### 4.2 Figures reconstruites depuis `figure-data`

Certaines figures sont stockées sous forme de fragments texte Base64 :

`assets/figure-data/<nom>.part-00.txt`, `part-01.txt`, etc.

Une page les appelle avec des attributs de type :

```html
<img data-b64-name="nom-de-la-figure" data-b64-parts="3" data-b64-mime="image/webp" ...>
```

`figure-loader.js` récupère tous les fragments, les concatène, décode le Base64, crée un `Blob` et remplace la source de l’image. La version anglaise utilise `en/figure-loader.js`, identique dans son fonctionnement mais avec le chemin relatif `../assets/figure-data/`.

Conséquences importantes :

- ne jamais supprimer un fragment isolé d’une série active ;
- `data-b64-parts` doit correspondre au nombre exact de fragments attendus ;
- une figure peut être absente des références `src=` classiques tout en étant indispensable au site ;
- après toute intervention sur `figure-data`, vérifier que toutes les séquences demandées par le HTML sont complètes et non vides.

## 5. Cas particulier PyAges

Deux images PyAges ont des fonctions différentes :

- `assets/pyages-software-figure.png` est utilisée sur les pages Logiciels / Software.
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

`.github/workflows/verify-pyages-live.yml` vérifie après déploiement que `assets/pyages-software-figure.png` est bien une image PNG substantielle et que les pages FR/EN la référencent correctement.

## 6. Bibliographie complète

La page `bibliographie.html` et son équivalent anglais chargent la bibliographie côté navigateur.

### Source principale

Les cinq fichiers `bibliographie-payload-01.txt` à `bibliographie-payload-05.txt` contiennent ensemble un document HTML compressé avec gzip puis encodé en Base64.

`bibliography-loader.js` :

1. charge les cinq fragments ;
2. concatène et décode le Base64 ;
3. décompresse le gzip via `DecompressionStream` ;
4. insère le HTML dans la page ;
5. applique plusieurs normalisations et ajustements éditoriaux FR/EN ;
6. gère actuellement certains éléments « en préparation », « soumis », « en révision » et quelques ajouts récents explicites.

Les payloads ne sont donc pas de simples fichiers texte à éditer ligne par ligne. Ne pas les modifier à la main sans reconstruire correctement le contenu gzip/Base64.

### Ajustements et enrichissements

`bibliography-updates.js` contient des mises à jour ciblées et des enrichissements éditoriaux. Il interroge notamment Crossref pour une publication précise et ajoute des liens contextuels à certaines publications.

`bibliography-hal.js` interroge l’API HAL et ajoute, lorsque c’est possible, un lien `[HAL]` aux entrées correspondantes. Cette étape est volontairement facultative : si HAL est indisponible, la bibliographie doit rester utilisable.

Lors d’une future mise à jour bibliographique, vérifier non seulement les payloads mais aussi les ajustements explicites présents dans `bibliography-loader.js` et `bibliography-updates.js`, afin d’éviter doublons ou informations devenues obsolètes.

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

### Pages volontairement non indexées

Les galeries scientifiques :

- `galerie-recherche.html`
- `en/research-figures.html`

sont volontairement en `noindex,follow`. Elles restent accessibles depuis le site mais ne doivent **pas** être présentes dans `sitemap.xml`.

### Sitemap

À l’état de référence de septembre 2026, `sitemap.xml` contient exactement 36 URL, soit toutes les pages indexables et seulement celles-ci.

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
- intégrité des fragments `figure-data` si une figure dynamique est concernée ;
- payloads et scripts de bibliographie si la bibliographie change ;
- absence d’asset devenu orphelin si une image est remplacée.

### Après publication

Pour une modification importante, contrôler au minimum :

- que les pages modifiées répondent en HTTP 200 ;
- que les assets modifiés sont effectivement publiés ;
- que les figures dynamiques chargent leurs fragments ;
- que le sitemap publié correspond au fichier du dépôt.

GitHub Pages peut avoir un court délai de propagation après un push.

## 11. Liens externes

Un contrôle automatique des liens externes est utile, mais ses résultats doivent être interprétés avec prudence.

Des sites comme DOI/Crossref, LinkedIn, Google Scholar, OSERen, certains éditeurs scientifiques ou ResearchGate peuvent renvoyer `403`, `429` ou `999` à un robot tout en fonctionnant normalement dans un navigateur.

Ne jamais supprimer ou remplacer un lien externe uniquement parce qu’un test automatisé reçoit un refus anti-bot. Vérifier manuellement ou par une autre source lorsqu’un lien semble réellement mort.

## 12. État de référence après l’audit du 14 septembre 2026

Cet état sert de point de comparaison, pas d’invariant éternel : les nombres pourront légitimement évoluer si le site s’enrichit.

- 40 fichiers HTML au total.
- 20 pages FR et 20 pages EN.
- 20 couples de pages décrits dans `mirror-map.json`.
- 38 pages de contenu et 2 pages de redirection.
- 36 pages indexables dans `sitemap.xml`.
- 2 pages `noindex,follow` : les galeries scientifiques FR/EN.
- 674 références locales validées.
- 0 asset normal orphelin.
- 14 familles `assets/figure-data` utilisées.
- 13 familles de figures dynamiques chargées par le HTML, représentant 34 fragments actifs.
- 9 fragments source PyAges supplémentaires utilisés pour reconstruire l’image WebP.
- 4 workflows GitHub Actions permanents.
- Lors du dernier audit, 158 URL externes distinctes étaient présentes ; les refus automatisés provenaient essentiellement de mécanismes anti-bot et non de liens manifestement cassés.

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
