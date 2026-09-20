#!/usr/bin/env python3
"""Apply the September 2026 content, accessibility and SEO audit updates.

The script is deliberately idempotent so the global conventions can be applied again
after adding a bilingual page.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EMAIL = "jean-raynald.de-dreuzy@univ-rennes.fr"
ORCID = "https://orcid.org/0000-0003-2993-2015"
HAL = 'https://hal.science/search/index/?q=%22Jean-Raynald%20de%20Dreuzy%22'
DEFAULT_SOCIAL_IMAGE = "https://dreuzy.github.io/assets/figures/futureflow-framework.webp"

B64_DIMS = {
    "stream-calibration-illustration": (720, 540),
    "reactivity-illustration": (900, 675),
    "climate-streams-illustration": (720, 540),
    "hydromodpy-final": (720, 540),
    "futureflow-illustration": (1000, 625),
    "onewater-sentinel": (900, 422),
    "gallery-ploemeur-transit-2014": (380, 255),
    "gallery-breville-water-table": (380, 188),
    "gallery-surface-subsurface-marcais-2017": (380, 133),
    "gallery-thermal-bernardie-2018": (247, 430),
    "gallery-phes-poulain-2018": (380, 162),
}

REMOTE_DIMS = {
    "hess-27-3221-2023-f01-thumb.png": (500, 258),
    "hess-27-3221-2023-f02-thumb.png": (500, 160),
    "hess-27-3221-2023-f03-thumb.png": (500, 166),
    "hess-24-633-2020-f01-thumb.png": (500, 406),
    "hess-24-633-2020-f02-thumb.png": (500, 588),
    "hess-24-633-2020-f03-thumb.png": (500, 429),
    "hess-24-633-2020-f04-thumb.png": (500, 493),
    "hess-30-5571-2026-f01-thumb.png": (500, 307),
    "hess-30-5571-2026-f02-thumb.jpg": (500, 333),
    "hess-30-5571-2026-f03-thumb.png": (500, 354),
    "flow-in-2d-fracture-networks-l.jpg": (1024, 768),
    "avatars.githubusercontent.com": (460, 460),
    "BD-Normandie-Nappes_004-1.jpg": (1609, 923),
    "9782271152220.jpg.webp": (600, 757),
}

LOCAL_DIMS = {
    "futureflow-framework.webp": (1000, 625),
    "hydromodpy-approved.webp": (1448, 1086),
    "onewater.svg": (900, 422),
    "eau-territoire.webp": (1832, 859),
    "fractured-media-channeling.webp": (1536, 1024),
    "gallery-coastal-aquifer.svg": (900, 560),
    "gallery-ploemeur-transit-times.svg": (900, 560),
    "pyages-groundwater-age-v2.webp": (980, 735),
    "pyages-software-figure.webp": (1448, 1086),
    "maquette-nappes.jpg": (240, 160),
    "maquette-fractures.jpg": (145, 177),
    "embedded/stream-calibration-illustration.webp": (720, 540),
    "embedded/reactivity-illustration.webp": (900, 675),
    "embedded/climate-streams-illustration.webp": (720, 540),
    "embedded/hydromodpy-final.webp": (720, 540),
    "embedded/gallery-ploemeur-transit-2014.webp": (380, 255),
    "embedded/gallery-breville-water-table.webp": (380, 188),
    "embedded/gallery-surface-subsurface-marcais-2017.webp": (380, 133),
    "embedded/gallery-thermal-bernardie-2018.webp": (247, 430),
    "embedded/gallery-phes-poulain-2018.webp": (380, 162),
}


def add_meta(soup: BeautifulSoup, *, prop: str | None = None, name: str | None = None, content: str) -> None:
    selector = f'meta[property="{prop}"]' if prop else f'meta[name="{name}"]'
    if soup.select_one(selector):
        return
    tag = soup.new_tag("meta")
    if prop:
        tag["property"] = prop
    else:
        tag["name"] = name
    tag["content"] = content
    soup.head.append(tag)


def footer_fragment(soup: BeautifulSoup, is_en: bool) -> Tag:
    inner = soup.new_tag("div", attrs={"class": "inner"})
    identity = soup.new_tag("span")
    identity.string = "Jean-Raynald de Dreuzy · CNRS · Géosciences Rennes · ENS Rennes"
    contact = soup.new_tag("span", attrs={"class": "footer-contact"})
    mail = soup.new_tag("a", href=f"mailto:{EMAIL}")
    mail.string = "Email" if is_en else "Courriel"
    orcid = soup.new_tag("a", href=ORCID, target="_blank", rel="me noopener")
    orcid.string = "ORCID"
    hal = soup.new_tag("a", href=HAL, target="_blank", rel="noopener")
    hal.string = "HAL"
    contact.extend([mail, NavigableString(" · "), orcid, NavigableString(" · "), hal])
    inner.extend([identity, contact])
    return inner


def intrinsic_dimensions(page: Path, img: Tag) -> tuple[int, int] | None:
    b64_name = img.get("data-b64-name", "")
    if b64_name in B64_DIMS:
        return B64_DIMS[b64_name]
    src = img.get("src", "")
    for token, dims in LOCAL_DIMS.items():
        if src.endswith(token):
            return dims
    for token, dims in REMOTE_DIMS.items():
        if token in src:
            return dims
    if "pnas-2019/figure-01.jpg" in src:
        return (805, 938)
    if "pnas-2019/figure-02.jpg" in src:
        return (796, 799)
    if "pnas-2019/figure-03.jpg" in src:
        return (673, 849)
    if "publications-au-fil-du-temps.svg" in src:
        return (1249, 751)
    if not src or src.startswith(("http://", "https://", "data:")):
        return None
    target = (page.parent / src.split("?", 1)[0].split("#", 1)[0]).resolve()
    if not target.exists():
        return None
    try:
        with Image.open(target) as image:
            return image.size
    except Exception:
        text = target.read_text(encoding="utf-8", errors="ignore") if target.suffix.lower() == ".svg" else ""
        view_box = re.search(r'viewBox=["\']\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)', text)
        if view_box:
            return (round(float(view_box.group(1))), round(float(view_box.group(2))))
        width = re.search(r'\bwidth=["\']([\d.]+)', text)
        height = re.search(r'\bheight=["\']([\d.]+)', text)
        if width and height:
            return (round(float(width.group(1))), round(float(height.group(1))))
    return None


def remove_section_from_heading(heading: Tag) -> None:
    node = heading.next_sibling
    while node:
        nxt = node.next_sibling
        if isinstance(node, Tag) and node.name in {"h2", "h3"}:
            break
        node.extract()
        node = nxt
    heading.decompose()


def add_publication_over_time_table(soup: BeautifulSoup, is_en: bool) -> None:
    main = soup.main
    if not main or main.select_one(".publication-summary"):
        return
    data = json.loads((ROOT / "publications-au-fil-du-temps-data.json").read_text(encoding="utf-8"))
    intro = soup.new_tag("p", attrs={"class": "lead publication-summary"})
    intro.string = (
        "The record covers 114 journal articles, 256 conference abstracts and 14 proceedings. "
        "The strongest annual article output was in 2010 (11 papers); conference abstracts peaked in 2018 (24)."
        if is_en else
        "Le corpus comprend 114 articles, 256 abstracts de colloques et 14 proceedings. "
        "Le maximum annuel d’articles a été atteint en 2010 (11 articles) ; celui des abstracts en 2018 (24)."
    )
    figure = main.find("figure")
    if figure:
        figure.insert_before(intro)
    details = soup.new_tag("details", attrs={"class": "data-details"})
    summary = soup.new_tag("summary")
    summary.string = "Show the annual data table" if is_en else "Afficher le tableau annuel des données"
    details.append(summary)
    wrapper = soup.new_tag("div", attrs={"class": "comparison-table", "role": "region", "tabindex": "0"})
    wrapper["aria-label"] = "Annual publication data" if is_en else "Données annuelles de publication"
    table = soup.new_tag("table")
    caption = soup.new_tag("caption")
    caption.string = "Annual counts by output type" if is_en else "Nombre annuel par type de production"
    table.append(caption)
    thead = soup.new_tag("thead")
    tr = soup.new_tag("tr")
    for label in (("Year", "Articles", "Abstracts", "Proceedings") if is_en else ("Année", "Articles", "Abstracts", "Proceedings")):
        th = soup.new_tag("th", scope="col")
        th.string = label
        tr.append(th)
    thead.append(tr)
    table.append(thead)
    tbody = soup.new_tag("tbody")
    years = sorted({*data["articles"], *data["abstracts"], *data["proceedings"]}, key=int)
    for year in years:
        row = soup.new_tag("tr")
        th = soup.new_tag("th", scope="row")
        th.string = year
        row.append(th)
        for series in ("articles", "abstracts", "proceedings"):
            td = soup.new_tag("td")
            td.string = str(data[series].get(year, 0))
            row.append(td)
        tbody.append(row)
    table.append(tbody)
    wrapper.append(table)
    details.append(wrapper)
    if figure:
        figure.insert_after(details)
    else:
        main.append(details)


def add_rivages_selected_publication(soup: BeautifulSoup, is_en: bool) -> None:
    section = soup.select_one("#pub-change")
    section_heading = section.find("h2") if section else None
    if not section or not section_heading:
        return
    existing = next((entry for entry in soup.select(".pub-entry") if "Rivages Normands 2100: transdisciplinary" in entry.get_text(" ", strip=True)), None)
    if existing:
        section_heading.insert_after(existing.extract())
        return
    entry = soup.new_tag("div", attrs={"class": "pub-entry"})
    title = soup.new_tag("div", attrs={"class": "pub-title"})
    link = soup.new_tag("a", href="https://doi.org/10.1007/s11625-026-01896-8")
    link.string = "Rivages Normands 2100: transdisciplinary co-constructed knowledge for land-use adaptation to groundwater rise along Normandy coastline"
    title.append(link)
    meta = soup.new_tag("div", attrs={"class": "pub-meta"})
    meta.append(NavigableString("M. Le Mesnil et al. (2026) · "))
    journal = soup.new_tag("span", attrs={"class": "smallcaps"})
    journal.string = "Sustainability Science"
    meta.extend([journal, NavigableString(" · published online 8 September 2026" if is_en else " · publié en ligne le 8 septembre 2026")])
    entry.extend([title, meta])
    section_heading.insert_after(entry)


def page_specific(soup: BeautifulSoup, rel: str, is_en: bool) -> None:
    if rel in {"projets.html", "en/projects.html"}:
        soup.title.string = ("Projects & grants — Jean-Raynald de Dreuzy" if is_en else "Projets & contrats — Jean-Raynald de Dreuzy")
        og_title = soup.select_one('meta[property="og:title"]')
        twitter_title = soup.select_one('meta[name="twitter:title"]')
        for meta in (og_title, twitter_title):
            if meta:
                meta["content"] = soup.title.string
        h1 = soup.find("h1")
        if h1:
            h1.string = "Projects & grants" if is_en else "Projets & contrats"
        lead = soup.select_one("main > .lead")
        if lead:
            lead.string = (
                "Current research grants and programmes, followed by a documented selection of major completed projects."
                if is_en else
                "Contrats et programmes de recherche en cours, puis sélection documentée des principaux projets achevés."
            )
        future = soup.select_one("#futureflow")
        if future:
            for p in future.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text.startswith("Participants"):
                    p.clear(); p.append(BeautifulSoup(
                        "<strong>Participants</strong> — Arnaud Blouin, Benoît Combemale, Alexandre Boisson, Florence Habets, Clément Roques, Philip Brunner and Oliver Schilling."
                        if is_en else
                        "<strong>Participants</strong> — Arnaud Blouin, Benoît Combemale, Alexandre Boisson, Florence Habets, Clément Roques, Philip Brunner et Oliver Schilling.", "html.parser"))
                elif text.startswith("Institutions"):
                    p.clear(); p.append(BeautifulSoup(
                        "<strong>Institutions</strong> — CNRS / University of Rennes · University of Neuchâtel · BRGM · University of Basel · ENS-PSL · IRISA collaboration"
                        if is_en else
                        "<strong>Institutions</strong> — CNRS / Université de Rennes · Université de Neuchâtel · BRGM · Université de Bâle · ENS-PSL · collaboration IRISA", "html.parser"))
            if not future.select_one("a.detail-link"):
                p = soup.new_tag("p")
                a = soup.new_tag("a", href="futureflow.html", attrs={"class": "detail-link"})
                a.string = "Project details →" if is_en else "Détail du projet →"
                p.append(a)
                future.find("div").append(p)
        onewater = soup.select_one("#onewater .meta-line")
        if onewater:
            html = str(onewater).replace(" · 2023–", " · programme 2022– · ANR contract 2023–" if is_en else " · programme 2022– · contrat ANR 2023–")
            onewater.replace_with(BeautifulSoup(html, "html.parser").find("div"))
        chair = soup.select_one("#water-territories")
        if chair:
            for p in chair.find_all("p"):
                if p.get_text(" ", strip=True).startswith(("Programmes",)):
                    p.clear(); p.append(BeautifulSoup(
                        "<strong>Programmes</strong> — initial phase 2019–2023 · current programme 2024–2028"
                        if is_en else
                        "<strong>Programmes</strong> — phase initiale 2019–2023 · programme actuel 2024–2028", "html.parser"))
        nirecas = soup.select_one("#nirecas")
        if nirecas:
            paragraphs = [n for n in nirecas.contents if isinstance(n, NavigableString)]
            for node in paragraphs:
                if "300" in str(node):
                    node.replace_with(
                        "Assessing and mapping nitrate recovery capacity by linking reactivity, agricultural legacy, transit times and lithology across 200 pilot sites in the Armorican Massif, before extending the approach to other European regions."
                        if is_en else
                        "Évaluer et cartographier la capacité de récupération vis-à-vis des nitrates en reliant réactivité, héritage des pratiques agricoles, temps de transfert et lithologie à partir de 200 sites pilotes dans le Massif armoricain, avant extension à d’autres régions européennes."
                    )
        archange = soup.select_one("#archange")
        coastal_href = "coastal-risks.html" if is_en else "risques-cotiers.html"
        if archange and not archange.select_one("a.detail-link"):
            a = soup.new_tag("a", href=coastal_href, attrs={"class": "detail-link"})
            a.string = "RIVAGES → ARCHANGE: details" if is_en else "RIVAGES → ARCHANGE : en détail"
            archange.append(soup.new_tag("br")); archange.append(a)
        elif archange and archange.select_one("a.detail-link"):
            archange.select_one("a.detail-link")["href"] = coastal_href
        earlier = soup.select_one("#earlier-projects")
        if earlier:
            for block in earlier.select(".secondary-project"):
                text = block.get_text(" ", strip=True)
                if text.startswith("RIVAGES Normands 2100") and not block.select_one("a.detail-link"):
                    a = soup.new_tag("a", href=coastal_href, attrs={"class": "detail-link"})
                    a.string = "RIVAGES → ARCHANGE: details" if is_en else "RIVAGES → ARCHANGE : en détail"
                    block.append(soup.new_tag("br")); block.append(a)
                if text.startswith(("EAUX2050", "EAUX 2050")):
                    for node in block.find_all(string=True):
                        node.replace_with(str(node).replace("EAUX2050", "EAUX 2050").replace("EAUX2070", "RIVIÈRES 2070").replace(" & ", " / ").replace("2019–2024", "2019–2026"))
                    if not block.select_one("a.detail-link"):
                        a = soup.new_tag("a", href=("water-2050-rivers-2070-cydre.html" if is_en else "eaux-2050-rivieres-2070-cydre.html"), attrs={"class": "detail-link"})
                        a.string = "Programme details and final report" if is_en else "Détail des programmes et rapport final"
                        block.append(soup.new_tag("br")); block.append(a)
            for link in earlier.select("a.detail-link"):
                if "RIVAGES" in link.get_text():
                    link["href"] = coastal_href
                if "rapport" in link.get_text().lower() or "report" in link.get_text().lower():
                    link["href"] = "water-2050-rivers-2070-cydre.html" if is_en else "eaux-2050-rivieres-2070-cydre.html"

    if rel in {"equipe.html", "en/team.html"}:
        former_label = "Former Master's students" if is_en else "Anciens Masters"
        former = next((h for h in soup.find_all("h2") if h.get_text(" ", strip=True) == former_label), None)
        if former:
            remove_section_from_heading(former)
        current_label = "Master's students" if is_en else "Masters"
        current = next((h for h in soup.find_all("h2") if h.get_text(" ", strip=True) == current_label), None)
        if current and not soup.select_one(".masters-archive-link"):
            next_heading = current.find_next("h2")
            note = soup.new_tag("p", attrs={"class": "notice masters-archive-link"})
            link = soup.new_tag("a", href="masters.html")
            link.string = "See the full archive of former Master's students and interns →" if is_en else "Voir l’archive complète des anciens Masters et stagiaires →"
            note.append(link)
            if next_heading:
                next_heading.insert_before(note)

    if rel in {"masters.html", "en/masters.html"}:
        for topic in soup.select(".people-entry .topic"):
            if topic.get_text(" ", strip=True) == "Modeling the crystalline aquifer of Ploemeur" and not is_en:
                topic.string = "Modélisation de l’aquifère cristallin de Plœmeur"

    if rel in {"publications.html", "en/publications.html"}:
        add_rivages_selected_publication(soup, is_en)

    if rel in {"publications-au-fil-du-temps.html", "en/publications-over-time.html"}:
        add_publication_over_time_table(soup, is_en)

    if rel in {"cv.html", "en/cv.html"} and not soup.select_one(".download-cv"):
        h1 = soup.find("h1")
        if h1:
            p = soup.new_tag("p", attrs={"class": "download-cv"})
            link = soup.new_tag("a", href=("../assets/cv/CV_Jean-Raynald_de_Dreuzy_2026.pdf" if is_en else "assets/cv/CV_Jean-Raynald_de_Dreuzy_2026.pdf"))
            link.string = "Download the CV (PDF, French)" if is_en else "Télécharger le CV (PDF)"
            p.append(link)
            h1.insert_after(p)


def transform_page(page: Path) -> None:
    rel = page.relative_to(ROOT).as_posix()
    is_en = rel.startswith("en/")
    html = page.read_text(encoding="utf-8")
    html = html.replace("assets/figures/eau-territoire.png", "assets/figures/eau-territoire.webp")
    html = html.replace("assets/figures/fractured-media-channeling.png", "assets/figures/fractured-media-channeling.webp")
    html = html.replace("assets/pyages-software-figure.png", "assets/pyages-software-figure.webp")
    html = html.replace(
        "Flow simulation in 3D multi-scale fractured networks using non-matching meshes",
        "A Generalized Mixed Hybrid Mortar Method for Solving Flow in Stochastic Discrete Fracture Networks",
    ).replace(
        "G. Pichot, J.-R. de Dreuzy &amp; J. Erhel (2012)",
        "G. Pichot, J. Erhel &amp; J.-R. de Dreuzy (2012)",
    )
    html = html.replace("https://h2olab.inria.fr/", "https://radar.inria.fr/report/2009/sage/uid75.html")
    html = html.replace("https://anr.fr/Project-ANR-", "https://anr.fr/Projet-ANR-")
    pnas_prefix = "../" if is_en else ""
    html = re.sub(
        r'https://www\.pnas\.org/cms/10\.1073/pnas\.1816892116/asset/[^"\']+/assets/graphic/pnas\.1816892116fig01\.jpeg',
        f"{pnas_prefix}assets/figures/pnas-2019/figure-01.jpg", html,
    )
    html = re.sub(
        r'https://www\.pnas\.org/cms/10\.1073/pnas\.1816892116/asset/[^"\']+/assets/graphic/pnas\.1816892116fig02\.jpeg',
        f"{pnas_prefix}assets/figures/pnas-2019/figure-02.jpg", html,
    )
    html = re.sub(
        r'https://www\.pnas\.org/cms/10\.1073/pnas\.1816892116/asset/[^"\']+/assets/graphic/pnas\.1816892116fig03\.jpeg',
        f"{pnas_prefix}assets/figures/pnas-2019/figure-03.jpg", html,
    )
    soup = BeautifulSoup(html, "html.parser")

    # Lightweight redirect pages must not compete with the canonical CV pages in search results.
    if rel in {"a-propos.html", "en/about.html"} and not soup.select_one('meta[name="robots"]'):
        robots = soup.new_tag("meta", attrs={"name": "robots", "content": "noindex,follow"})
        soup.head.append(robots)

    # Navigation wording and keyboard/screen-reader support.
    for link in soup.select(".nav-links a"):
        label = link.get_text(" ", strip=True)
        if (not is_en and label == "Projets") or (is_en and label == "Projects"):
            link.string = "Projects & grants" if is_en else "Projets & contrats"
        if "active" in link.get("class", []):
            active_target = Path(link.get("href", "").split("#", 1)[0]).name
            link["aria-current"] = "page" if active_target == page.name else "location"
    nav = soup.select_one(".nav-links")
    if nav and not nav.get("aria-label"):
        nav["aria-label"] = "Main navigation" if is_en else "Navigation principale"
    main = soup.find("main")
    if main:
        main["id"] = "main-content"
        if not soup.select_one(".skip-link"):
            skip = soup.new_tag("a", href="#main-content", attrs={"class": "skip-link"})
            skip.string = "Skip to content" if is_en else "Aller au contenu"
            soup.body.insert(0, skip)

    # Site icon and complete social metadata.
    if soup.head and not soup.select_one('link[rel="icon"]'):
        icon = soup.new_tag("link", rel="icon", href=("../favicon.svg" if is_en else "favicon.svg"), type="image/svg+xml")
        soup.head.append(icon)
    if main and "noindex" not in (soup.select_one('meta[name="robots"]') or {}).get("content", ""):
        title = soup.title.get_text(strip=True) if soup.title else "Jean-Raynald de Dreuzy"
        description = (soup.select_one('meta[name="description"]') or {}).get("content", "")
        canonical = (soup.select_one('link[rel="canonical"]') or {}).get("href", "")
        add_meta(soup, prop="og:type", content="website")
        add_meta(soup, prop="og:site_name", content="Jean-Raynald de Dreuzy")
        add_meta(soup, prop="og:title", content=title)
        add_meta(soup, prop="og:description", content=description)
        add_meta(soup, prop="og:url", content=canonical)
        add_meta(soup, prop="og:locale", content="en_US" if is_en else "fr_FR")
        add_meta(soup, prop="og:image", content=DEFAULT_SOCIAL_IMAGE)
        add_meta(soup, name="twitter:card", content="summary_large_image")
        add_meta(soup, name="twitter:title", content=title)
        add_meta(soup, name="twitter:description", content=description)
        og_image = soup.select_one('meta[property="og:image"]')["content"]
        if "avatars.githubusercontent.com" in og_image:
            social_width, social_height = "460", "460"
            social_alt = "Portrait of Jean-Raynald de Dreuzy" if is_en else "Portrait de Jean-Raynald de Dreuzy"
        elif "pyages-groundwater-age-v2.webp" in og_image:
            social_width, social_height = "980", "735"
            social_alt = "PyAges groundwater-age modelling" if is_en else "Modélisation des âges des eaux souterraines avec PyAges"
        else:
            social_width, social_height = "1000", "625"
            social_alt = "FutureFlow multi-fidelity groundwater modelling framework" if is_en else "Cadre de modélisation multi-fidélité de FutureFlow"
        for prop, value in (("og:image:width", social_width), ("og:image:height", social_height), ("og:image:alt", social_alt)):
            add_meta(soup, prop=prop, content=value)
            soup.select_one(f'meta[property="{prop}"]')["content"] = value
        add_meta(soup, name="twitter:image", content=og_image)
        soup.select_one('meta[name="twitter:image"]')["content"] = og_image
        add_meta(soup, name="twitter:image:alt", content=social_alt)
        soup.select_one('meta[name="twitter:image:alt"]')["content"] = social_alt

    # The galleries contain unique, descriptive scientific content and should be indexed.
    if rel in {"galerie-recherche.html", "en/research-figures.html"}:
        robots = soup.select_one('meta[name="robots"]')
        if robots:
            robots.decompose()
        # Remove a corrupted legacy figure, and replace another with a stable local synthesis image.
        broken = soup.select_one('img[data-b64-name="gallery-pleine-fougeres-kolbe-2016"]')
        if broken:
            card = broken.find_parent("figure")
            if card:
                card.decompose()
        fractured = soup.select_one('img[data-b64-name="gallery-fractured-dreuzy-2012"]')
        if fractured:
            fractured.attrs.pop("data-b64-name", None)
            fractured.attrs.pop("data-b64-parts", None)
            fractured.attrs.pop("data-b64-mime", None)
            fractured["src"] = ("../" if is_en else "") + "assets/figures/fractured-media-channeling.webp"
            source = fractured.find_parent("figure").select_one(".figure-source")
            if source:
                source.string = (
                    "Synthesis illustration after de Dreuzy, Méheust & Pichot, Journal of Geophysical Research: Solid Earth, 2012."
                    if is_en else
                    "Illustration de synthèse d’après de Dreuzy, Méheust & Pichot, Journal of Geophysical Research: Solid Earth, 2012."
                )

    # A CNRS-hosted 2014 slide deck now returns a server error: retain the reference without a dead link.
    for link in soup.select('a[href*="2014-01_gaz_de_schiste_cnrs_de_dreuzy.pdf"]'):
        link.replace_with(NavigableString(link.get_text(" ", strip=True)))

    # Footer contact points are available on every content page.
    footer = soup.select_one("footer.preview-footer")
    if footer:
        footer.clear()
        footer.append(footer_fragment(soup, is_en))

    page_specific(soup, rel, is_en)

    # Intrinsic dimensions prevent layout shifts. All images also get asynchronous decoding.
    missing_dimensions: list[str] = []
    for img in soup.select("img"):
        dims = intrinsic_dimensions(page, img)
        if dims:
            img["width"], img["height"] = map(str, dims)
        else:
            missing_dimensions.append(img.get("src") or img.get("data-b64-name") or "<unknown>")
        if not img.has_attr("decoding"):
            img["decoding"] = "async"
    if missing_dimensions:
        raise RuntimeError(f"{rel}: missing intrinsic dimensions for {sorted(set(missing_dimensions))}")

    page.write_text(str(soup), encoding="utf-8")


def main() -> None:
    pages = sorted(ROOT.glob("*.html")) + sorted((ROOT / "en").glob("*.html"))
    for page in pages:
        transform_page(page)
    print(f"Updated {len(pages)} HTML pages.")


if __name__ == "__main__":
    main()
