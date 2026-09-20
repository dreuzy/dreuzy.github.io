#!/usr/bin/env python3
"""Build the complete bilingual bibliography as static, indexable HTML."""

from __future__ import annotations

import base64
import gzip
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
PAYLOADS = [ROOT / f"bibliographie-payload-0{i}.txt" for i in range(1, 6)]
RIVAGES_DOI = "10.1007/s11625-026-01896-8"
ASSOCIATED_DOIS = {
    "10.1109/tac.2017.2701150",
    "10.1016/j.jhydrol.2014.01.064",
    "10.1029/2012jb009461",
    "10.1002/wrcr.20206",
    "10.1002/2013wr013722",
    "10.1029/2011wr011360",
    "10.1016/j.jhydrol.2012.06.052",
    "10.1029/2011wr011129",
    "10.1016/j.jconhyd.2010.03.004",
}

PREPARATION = [
    "J. Marçais, J.-R. de Dreuzy, H. V. Gupta, Groundwater flow contributions to streamflows predicted by a hydrogeomorphological wetness index: insights from synthetic experiments. <span class=\"smallcaps\">Comptes Rendus Géoscience — Sciences de la Planète</span>",
    "K. Brenner, Y. Qiang, J. Marçais, J.-R. de Dreuzy, An Integrated Double-Continuum Approach for Simulating Coupled Vertical Richards Flows and Lateral Boussinesq Flows. <span class=\"smallcaps\">Advances in Water Resources</span>",
    "T. Touzeau et al., Functional archetypes of shallow aquifers for sustaining stream low flows: balancing storage and transmissivity. <span class=\"smallcaps\">Comptes Rendus Géoscience — Sciences de la Planète</span>",
    "R. Abhervé et al., Stream networks reveal shallow aquifer transmissivity across European crystalline bedrock headwater catchments. <span class=\"smallcaps\">Geophysical Research Letters</span>",
    "B. Boivin et al., Identifying inflow, evaporation and seepage from reservoir water-level dynamics for water-resource management. <span class=\"smallcaps\">Water Resources Research</span>",
    "E. Le Carrer et al., Pesticide dynamics in agricultural catchments",
    "I. Issolah et al., A generic software architecture for aquifer simulation",
]

SUBMITTED = [
    "M. Ricau, R. Abhervé, H. Budzinski, C. Casenave, A. Chaumot, F. Courant, V. Dupraz, G. Fernandes, H. Fenet, E. Gomez, P. Gonzalez, G. Imfeld, J. Jaunat, G. Junqua, C. Kane, S. Lardy-Fontan, T. Le Borgne, B. Lopez, J. M.F. Martins, J. Molénat, S. Payraudeau, A. Togola, J. Tournebize, J.-R. de Dreuzy (2026), Sentinel water fingerprint: capturing hydrosystem dynamics for adaptive water management. <span class=\"smallcaps\">WIREs Water</span>",
    "J.-R. de Dreuzy, S. Leray, J. Marçais (2026), PyAges: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages. <span class=\"smallcaps\">Geoscientific Model Development</span>",
]

ENRICHMENTS = [
    (
        "Rivages Normands 2100: transdisciplinary co-constructed knowledge for land-use adaptation to groundwater rise along Normandy coastline",
        '<strong>Autour du projet :</strong> <a href="https://oseren.univ-rennes.fr/rivages-normands-2100-articles-de-presse" target="_blank" rel="noopener">OSERen — articles de presse, interviews et ressources</a>',
        '<strong>Project context:</strong> <a href="https://oseren.univ-rennes.fr/rivages-normands-2100-articles-de-presse" target="_blank" rel="noopener">OSERen — press coverage, interviews and resources</a>',
    ),
    (
        "Projected climate change impacts on groundwater–surface water connectivity in a compartmentalized mountain headwater bedrock aquifer",
        '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/des-sources-en-sursis-les-tetes-de-bassin-versant-des-pyrenees-dans-un-monde-plus-chaud" target="_blank" rel="noopener">OSERen — Des sources en sursis</a>',
        '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/des-sources-en-sursis-les-tetes-de-bassin-versant-des-pyrenees-dans-un-monde-plus-chaud" target="_blank" rel="noopener">OSERen — Pyrenean headwaters in a warmer world</a>',
    ),
    (
        "The diversity of researchers’ roles in sustainability science: the influence of project characteristics",
        '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/la-diversite-des-roles-des-chercheurs-dans-la-science-de-la-durabilite" target="_blank" rel="noopener">OSERen — rôles des chercheurs en science de la durabilité</a>',
        '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/la-diversite-des-roles-des-chercheurs-dans-la-science-de-la-durabilite" target="_blank" rel="noopener">OSERen — researchers’ roles in sustainability science</a>',
    ),
    (
        "Calibration of groundwater seepage against the spatial distribution of the stream network to assess catchment-scale hydraulic properties",
        '<strong>Distinction éditoriale :</strong> <a href="https://hess.copernicus.org/articles/27/3221/2023/" target="_blank" rel="noopener">Highlight paper</a> — <span class="smallcaps">Hydrology and Earth System Sciences</span>.',
        '<strong>Editorial distinction:</strong> <a href="https://hess.copernicus.org/articles/27/3221/2023/" target="_blank" rel="noopener">Highlight paper</a> — <span class="smallcaps">Hydrology and Earth System Sciences</span>.',
    ),
    (
        "Deep denitrification: Stream and groundwater biogeochemistry reveal contrasted but connected worlds above and below",
        '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/denitrification-profonde-biogeochimie-eaux-constraste" target="_blank" rel="noopener">OSERen — Dénitrification profonde</a>',
        '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/denitrification-profonde-biogeochimie-eaux-constraste" target="_blank" rel="noopener">OSERen — Deep denitrification</a>',
    ),
    (
        "A hillslope-scale aquifer-model to determine past agricultural legacy and future nitrate concentrations in rivers",
        '<strong>Autour de cette publication :</strong> <a href="https://oseren.univ-rennes.fr/actualites/quel-est-le-role-et-lheritage-des-pratiques-agricoles-passees-sur-levolution-et-le-futur" target="_blank" rel="noopener">OSERen — héritage des pratiques agricoles</a>',
        '<strong>About this publication:</strong> <a href="https://oseren.univ-rennes.fr/actualites/quel-est-le-role-et-lheritage-des-pratiques-agricoles-passees-sur-levolution-et-le-futur" target="_blank" rel="noopener">OSERen — legacy of past agricultural practices</a>',
    ),
    (
        "What do we need to predict groundwater nitrate recovery trajectories?",
        '<strong>Autour de cette publication :</strong> <a href="https://geosciences.univ-rennes.fr/actualites/de-quoi-avons-nous-besoin-pour-predire-la-resilience-des-eaux-souterraines-aux" target="_blank" rel="noopener">Géosciences Rennes — résilience des eaux souterraines aux nitrates</a>',
        '<strong>About this publication:</strong> <a href="https://geosciences.univ-rennes.fr/actualites/de-quoi-avons-nous-besoin-pour-predire-la-resilience-des-eaux-souterraines-aux" target="_blank" rel="noopener">Géosciences Rennes — groundwater recovery from nitrate contamination</a>',
    ),
    (
        "Stratification of reactivity determines nitrate removal in groundwater",
        '<strong>Autour de cette publication :</strong> <a href="https://www.espace-sciences.org/sciences-ouest/370/actualite/l-eau-souterraine-lavee-des-nitrates" target="_blank" rel="noopener">Espace des sciences — L’eau souterraine lavée des nitrates</a>',
        '<strong>About this publication:</strong> <a href="https://www.espace-sciences.org/sciences-ouest/370/actualite/l-eau-souterraine-lavee-des-nitrates" target="_blank" rel="noopener">Espace des sciences — L’eau souterraine lavée des nitrates</a>',
    ),
]


def norm(value: str) -> str:
    value = unicodedata.normalize("NFD", value or "")
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", value).strip().lower()


def load_source() -> BeautifulSoup:
    raw = "".join(path.read_text(encoding="utf-8") for path in PAYLOADS)
    html = gzip.decompress(base64.b64decode(re.sub(r"\s+", "", raw))).decode("utf-8")
    return BeautifulSoup(f'<div id="bibliography-static">{html}</div>', "html.parser")


def heading_level(tag: Tag) -> int:
    return int(tag.name[1])


def section_nodes(heading: Tag) -> list[Tag]:
    level = heading_level(heading)
    nodes: list[Tag] = []
    node = heading.find_next_sibling()
    while node:
        if isinstance(node, Tag) and re.fullmatch(r"h[1-6]", node.name) and heading_level(node) <= level:
            break
        if isinstance(node, Tag):
            nodes.append(node)
        node = node.find_next_sibling()
    return nodes


def remove_section(heading: Tag) -> None:
    for node in section_nodes(heading):
        node.decompose()
    heading.decompose()


def following_list(soup: BeautifulSoup, heading: Tag, unnumbered: bool = False) -> Tag:
    node = heading.find_next_sibling()
    while node and (not isinstance(node, Tag) or node.name not in {"ol", "ul", "h2", "h3"}):
        node = node.find_next_sibling()
    if not isinstance(node, Tag) or node.name in {"h2", "h3"}:
        node = soup.new_tag("ul" if unnumbered else "ol")
        heading.insert_after(node)
    if unnumbered and node.name == "ol":
        node.name = "ul"
    if unnumbered:
        classes = node.get("class", [])
        if "bib-unnumbered" not in classes:
            classes.append("bib-unnumbered")
        node["class"] = classes
    return node


def add_list_items(soup: BeautifulSoup, target: Tag, items: list[str], status: str) -> None:
    for html in reversed(items):
        li = soup.new_tag("li")
        fragment = BeautifulSoup(f"{html}, {status}.", "html.parser")
        li.extend(list(fragment.contents))
        target.insert(0, li)


def normalize_status_text(host: Tag, is_en: bool) -> None:
    replacements = (
        [
            (r"article en révision pour", "in revision for"), (r"article en révision", "in revision"),
            (r"en révision", "in revision"), (r"under review at", "in revision for"),
            (r"under review for", "in revision for"), (r"under review", "in revision"),
            (r"in review", "in revision"), (r"soumis à", "submitted to"), (r"soumis", "submitted"),
            (r"en préparation pour", "in preparation for"), (r"en préparation", "in preparation"),
        ] if is_en else [
            (r"under review at", "en révision pour"), (r"under review for", "en révision pour"),
            (r"under review", "en révision"), (r"in revision at", "en révision pour"),
            (r"in revision for", "en révision pour"), (r"in revision", "en révision"),
            (r"in review", "en révision"), (r"submitted to", "soumis à"), (r"submitted", "soumis"),
            (r"in preparation for", "en préparation pour"), (r"in preparation", "en préparation"),
        ]
    )
    for text in list(host.find_all(string=True)):
        value = str(text)
        for pattern, replacement in replacements:
            value = re.sub(pattern, replacement, value, flags=re.I)
        if value != str(text):
            text.replace_with(value)


def build(lang: str) -> BeautifulSoup:
    is_en = lang == "en"
    soup = load_source()
    host = soup.select_one("#bibliography-static")
    assert host

    for entry in host.select("li,p"):
        html = str(entry)
        html = html.replace("From Aqua Incognita to Aqua Cognita", "Headwater catchments: from aqua incognita to aqua cognita")
        html = html.replace("PyAge: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages", "PyAges: an extensible toolkit for lumped-parameter modeling of tracer-derived groundwater ages")
        replacement = BeautifulSoup(html, "html.parser").find(entry.name)
        if replacement:
            entry.replace_with(replacement)

    unwanted = [
        "towards a more comprehensive representation of hydrosystems in water footprint assessments",
        "technical note: hydromodpy",
        "groundwater flow contributions to streamflows predicted by a hydrogeomorphological wetness index: insights from synthetic experiments",
        "an integrated double-continuum approach for simulating coupled vertical richards flows and lateral boussinesq flows",
        "functional archetypes of shallow aquifers for sustaining stream low flows: balancing storage and transmissivity",
    ]
    for entry in list(host.select("li,p")):
        if any(title in norm(entry.get_text(" ", strip=True)) for title in unwanted):
            entry.decompose()

    for entry in host.select("li,p"):
        if "reading the aquifer in the stream: a unified framework" in norm(entry.get_text(" ", strip=True)):
            for text in list(entry.find_all(string=True)):
                if "Environmental Science Letters" in str(text):
                    text.replace_with(str(text).replace("Environmental Science Letters", ""))

    for heading in list(host.find_all(re.compile(r"^h[2-6]$"))):
        title = norm(heading.get_text(" ", strip=True))
        if "abandon" in title or "en preparation" in title or "in preparation" in title:
            remove_section(heading)

    section_names = {
        "articles-dans-des-revues-a-comite-de-lecture": "Peer-reviewed journal articles" if is_en else "Articles dans des revues à comité de lecture",
        "chapitre-douvrage": "Book chapter" if is_en else "Chapitre d’ouvrage",
        "rapports-et-autres-publications": "Reports and other publications" if is_en else "Rapports et autres publications",
        "abstracts-de-colloques": "Conference abstracts" if is_en else "Abstracts de colloques",
    }
    for ident, label in section_names.items():
        heading = host.select_one(f"#{ident}")
        if heading:
            heading.string = label

    indexed = host.select_one("#proceedings-references-dans-web-of-knowledge")
    nonindexed = host.select_one("#proceedings-non-references-dans-web-of-knowledge")
    if indexed:
        indexed.string = "Proceedings" if is_en else "Actes de colloques"
    if nonindexed:
        nonindexed.decompose()
    book = host.select_one("#chapitre-douvrage")
    if indexed and book:
        block = [indexed, *section_nodes(indexed)]
        for node in block:
            book.insert_before(node.extract())

    headings = host.find_all(re.compile(r"^h[2-6]$"))
    submitted = next((h for h in headings if "soumis" in norm(h.get_text()) or "submitted" in norm(h.get_text())), None)
    if not submitted:
        article_heading = host.select_one("#articles-dans-des-revues-a-comite-de-lecture")
        submitted = soup.new_tag("h3")
        submitted.string = "Submitted" if is_en else "Soumis"
        article_heading.insert_after(submitted)
    prep_heading = soup.new_tag("h3")
    prep_heading.string = "In preparation" if is_en else "En préparation"
    prep_list = soup.new_tag("ul", attrs={"class": "bib-list bib-unnumbered"})
    submitted.insert_before(prep_heading)
    prep_heading.insert_after(prep_list)
    add_list_items(soup, prep_list, PREPARATION, "in preparation" if is_en else "en préparation")
    submitted.string = "Submitted" if is_en else "Soumis"
    submitted_list = following_list(soup, submitted, unnumbered=True)
    add_list_items(soup, submitted_list, SUBMITTED, "submitted" if is_en else "soumis")

    normalize_status_text(host, is_en)
    for heading in host.find_all(re.compile(r"^h[2-6]$")):
        title = norm(heading.get_text(" ", strip=True))
        if title in {"in review", "in revision", "under review", "en revision"}:
            heading.string = "In revision" if is_en else "En révision"
            following_list(soup, heading, unnumbered=True)
        elif "articles publies" in title or title == "published":
            heading.string = "Published" if is_en else "Publiés"

    published = next((h for h in host.find_all(re.compile(r"^h[2-6]$")) if norm(h.get_text()) in {"published", "publies"}), None)
    assert published
    published_list = following_list(soup, published)
    for entry in list(published_list.find_all("li", recursive=False)):
        text = norm(entry.get_text(" ", strip=True))
        if "rivages normands 2100: transdisciplinary co-constructed knowledge" in text or RIVAGES_DOI in text:
            entry.decompose()
    hydromod = BeautifulSoup(
        'A. Gauvain, R. Abhervé, B. Boivin, C. Roques, M. Le Mesnil, A. Coche, T. Babey, J. Marçais, C. Bouchez, S. Leray, E. Marti, E. Bresciani, R. Figueroa, M. Pélissier, L. Guillaumot, T. Touzeau, I. Issolah, E. Maugan, R. S. Bagagnan, C. Vautier, J. Sallou, J. Bourcier, B. Combemale, P. Brunner, L. Longuevergne, L. Aquilina, J.-R. de Dreuzy (2026), <a href="https://hess.copernicus.org/articles/30/5571/2026/" target="_blank" rel="noopener">Technical note: HydroModPy (v1.0) – a Python toolbox for deploying catchment-scale shallow groundwater models</a>. <span class="smallcaps">Hydrology and Earth System Sciences</span>, 30, 5571.',
        "html.parser",
    )
    rivages = BeautifulSoup(
        f'M. Le Mesnil, F. Poirier, L. Aquilina, S. de Foville, A. Gauvain, F. Gresselin, F. Lemarchand, C. Harpet, F. Guibert, J.-R. de Dreuzy (2026), <a href="https://doi.org/{RIVAGES_DOI}" target="_blank" rel="noopener">Rivages Normands 2100: transdisciplinary co-constructed knowledge for land-use adaptation to groundwater rise along Normandy coastline</a>. <span class="smallcaps">Sustainability Science</span>, published online 8 September 2026.',
        "html.parser",
    )
    for fragment in (hydromod, rivages):
        li = soup.new_tag("li")
        li.extend(list(fragment.contents))
        published_list.insert(0, li)

    # The AGU 2006 abstract had inherited the HAL record of the separate EGU abstract.
    for entry in host.select("li"):
        text = norm(entry.get_text(" ", strip=True))
        if "well-test flow responses of highly heterogeneous porous and fractured media" in text and "agu fall meeting 2006" in text:
            for link in entry.select('a[href*="hal-00118414"]'):
                link.replace_with(NavigableString(link.get_text(" ", strip=True)))

    # A DOI reused in an abstract identifies the associated paper, not the abstract itself.
    abstracts_heading = host.select_one("#abstracts-de-colloques")
    if abstracts_heading:
        for node in section_nodes(abstracts_heading):
            for entry in node.select("li") if node.name in {"ol", "ul"} else []:
                for link in list(entry.select('a[href*="doi.org/"]')):
                    match = re.search(r"doi\.org/(10\.[^?#\s]+)", link.get("href", ""), flags=re.I)
                    doi = match.group(1).rstrip(".,;)").lower() if match else ""
                    if doi not in ASSOCIATED_DOIS:
                        continue
                    title = NavigableString(link.get_text(" ", strip=True))
                    associated = soup.new_tag("a", href=link["href"], target="_blank", rel="noopener", attrs={"class": "associated-article"})
                    associated.string = "[associated paper]" if is_en else "[article associé]"
                    link.replace_with(title, NavigableString(" "), associated)

    # Author bolding from the source is removed to keep every author typographically equal.
    for strong in list(host.select("li strong, li b, p strong, p b")):
        strong.unwrap()

    # Context links are embedded statically; HAL remains a progressive enhancement.
    entries = host.select("li")
    for title, fr_html, en_html in ENRICHMENTS:
        key = norm(title)
        entry = next((li for li in entries if key in norm(li.get_text(" ", strip=True))), None)
        if not entry:
            continue
        note = soup.new_tag("div", attrs={"class": "pub-meta"})
        fragment = BeautifulSoup(en_html if is_en else fr_html, "html.parser")
        note.extend(list(fragment.contents))
        entry.append(note)

    return soup


def update_page(path: Path, lang: str) -> None:
    page = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    built = build(lang)
    source = built.select_one("#bibliography-static")
    target = page.select_one("#bibliography-content")
    assert source and target
    target.clear()
    target["aria-busy"] = "false"
    for node in list(source.contents):
        target.append(node.extract())

    for script in list(page.select('script[src*="bibliography-loader.js"], script[src*="bibliography-updates.js"]')):
        script.decompose()

    toc = page.select_one(".bib-toc ul")
    if toc:
        proceedings = [li for li in toc.select("li") if "proceedings" in norm(li.get_text())]
        if proceedings:
            first = proceedings[0]
            link = first.find("a")
            if link:
                link.string = "Proceedings" if lang == "en" else "Actes de colloques"
            for duplicate in proceedings[1:]:
                duplicate.decompose()

    path.write_text(str(page), encoding="utf-8")


def main() -> None:
    update_page(ROOT / "bibliographie.html", "fr")
    update_page(ROOT / "en" / "bibliography.html", "en")
    print("Built static bibliography in French and English.")


if __name__ == "__main__":
    main()
