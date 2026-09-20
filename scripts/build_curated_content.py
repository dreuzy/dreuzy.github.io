#!/usr/bin/env python3
"""Apply repeatable editorial refinements to the bilingual hand-curated pages."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag


ROOT = Path(__file__).resolve().parents[1]


def soup_fragment(markup: str) -> BeautifulSoup:
    return BeautifulSoup(markup, "html.parser")


def append_fragment(parent: Tag, markup: str) -> None:
    fragment = soup_fragment(markup)
    parent.extend(list(fragment.contents))


def replace_contents(parent: Tag, markup: str) -> None:
    parent.clear()
    append_fragment(parent, markup)


def heading_section(page: BeautifulSoup, pattern: str) -> Tag | None:
    heading = page.find(["h2", "h3"], string=re.compile(pattern, re.IGNORECASE))
    return heading.find_parent("section") if heading else None


def replace_text_nodes(root: Tag, replacements: dict[str, str]) -> None:
    for node in list(root.find_all(string=True)):
        updated = str(node)
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != str(node):
            node.replace_with(updated)


HOME = {
    "fr": """
<div class="home-hero">
  <div class="home-copy">
    <div class="kicker">Hydrogéologie · ressources en eau · modélisation</div>
    <h1>Jean-Raynald de Dreuzy</h1>
    <div class="institution-signature"><a href="https://www.ens-rennes.fr/">École normale supérieure de Rennes</a><span aria-hidden="true">✜</span><a href="https://www.univ-rennes.fr/">Université de Rennes</a></div>
    <div class="home-role"><strong>Président de l’École normale supérieure de Rennes</strong> · depuis 2026</div>
    <div class="home-role"><strong>Directeur de recherche CNRS</strong><br/>Géosciences Rennes — Université de Rennes</div>
    <p>Je travaille sur les ressources en eau et les écoulements souterrains, de l’échelle du versant à l’échelle régionale. Mes recherches associent hydrogéologie, hydrologie et modélisation pour comprendre les transferts d’eau et de contaminants, leur relation avec les structures géologiques et géomorphologiques, et leur évolution sous l’effet du changement climatique.</p>
    <p class="home-responsibilities">Responsabilités actuelles et passées : président de l’ENS Rennes (depuis 2026) ; vice-président Recherche de l’ENS Rennes (2021–2026) ; directeur de l’OSERen (2017–2021) ; responsable de l’équipe EAU de Géosciences Rennes (2013–2016) et du groupe interdisciplinaire RISC-E (2014–2017).</p>
    <div class="tags"><span class="tag">Hydrogéologie</span><span class="tag">Bassins versants</span><span class="tag">Qualité de l’eau</span><span class="tag">Empreinte eau</span><span class="tag">Modélisation</span></div>
    <div class="quick-links"><a href="cv.html">CV</a><a href="https://hal.science/search/index/?q=%22Jean-Raynald%20de%20Dreuzy%22">HAL</a><a href="https://scholar.google.com/citations?hl=en&amp;user=5oB48GcAAAAJ">Google Scholar</a><a href="https://orcid.org/0000-0003-2993-2015">ORCID</a><a href="mailto:jean-raynald.de-dreuzy@ens-rennes.fr">Contact</a></div>
  </div>
  <div class="home-photo"><img alt="Portrait de Jean-Raynald de Dreuzy" decoding="async" height="460" src="assets/portrait-jean-raynald-de-dreuzy.jpg" width="460"/></div>
</div>
<div class="home-sections"><a href="recherche.html">Recherche</a><a href="projets.html">Projets</a><a href="equipe.html">Équipe</a><a href="publications.html">Publications</a><a href="logiciels.html">Logiciels</a><a href="science-societe.html">Science &amp; société</a><a href="cv.html">CV</a></div>
""",
    "en": """
<div class="home-hero">
  <div class="home-copy">
    <div class="kicker">Hydrogeology · water resources · modelling</div>
    <h1>Jean-Raynald de Dreuzy</h1>
    <div class="institution-signature"><a href="https://www.ens-rennes.fr/">École normale supérieure de Rennes</a><span aria-hidden="true">✜</span><a href="https://www.univ-rennes.fr/">University of Rennes</a></div>
    <div class="home-role"><strong>President of École normale supérieure de Rennes</strong> · since 2026</div>
    <div class="home-role"><strong>CNRS Research Director</strong><br/>Géosciences Rennes — University of Rennes</div>
    <p>I work on water resources and groundwater flow, from hillslope to regional scales. My research combines hydrogeology, hydrology and modelling to understand water and contaminant transport, its relationship with geological and geomorphological structures, and how it evolves under climate change.</p>
    <p class="home-responsibilities">Current and previous responsibilities: President of ENS Rennes (since 2026); Vice-President for Research at ENS Rennes (2021–2026); Director of OSERen (2017–2021); Head of the EAU team at Géosciences Rennes (2013–2016) and of the interdisciplinary RISC-E group (2014–2017).</p>
    <div class="tags"><span class="tag">Hydrogeology</span><span class="tag">Catchments</span><span class="tag">Water quality</span><span class="tag">Water footprint</span><span class="tag">Modelling</span></div>
    <div class="quick-links"><a href="cv.html">CV</a><a href="https://hal.science/search/index/?q=%22Jean-Raynald%20de%20Dreuzy%22">HAL</a><a href="https://scholar.google.com/citations?hl=en&amp;user=5oB48GcAAAAJ">Google Scholar</a><a href="https://orcid.org/0000-0003-2993-2015">ORCID</a><a href="mailto:jean-raynald.de-dreuzy@ens-rennes.fr">Contact</a></div>
  </div>
  <div class="home-photo"><img alt="Portrait of Jean-Raynald de Dreuzy" decoding="async" height="460" src="../assets/portrait-jean-raynald-de-dreuzy.jpg" width="460"/></div>
</div>
<div class="home-sections"><a href="research.html">Research</a><a href="projects.html">Projects</a><a href="team.html">Team</a><a href="publications.html">Publications</a><a href="software.html">Software</a><a href="science-society.html">Science &amp; society</a><a href="cv.html">CV</a></div>
""",
}


COLLABORATIONS = {
    "fr": """
<p class="collab-list"><strong>Luc Aquilina</strong> · <strong>Laurent Longuevergne</strong> · <strong>Tanguy Le Borgne</strong> · <strong>Thierry Labasque</strong> · <strong>Jean de Brémond d'Ars</strong> · <strong>Camille Bouchez</strong> · <strong>Hélène Hivert</strong> · <strong>Camille Vautier</strong> · <strong>Pierre Brigode</strong> (Géosciences Rennes, Université de Rennes), <strong>Ronan Abhervé</strong> · <strong>Rémi Dupas</strong> (SAS, INRAE), <strong>Arnaud Blouin</strong> · <strong>Benoît Combemale</strong> (DIVERSE, IRISA, Inria), <strong>Alexandre Boisson</strong> · <strong>Anne Togola</strong> (BRGM), <strong>Clément Roques</strong> · <strong>Philip Brunner</strong> (CHYN, Université de Neuchâtel, Suisse), <strong>Florence Habets</strong> (Laboratoire de Géologie de l’ENS, ENS-PSL), <strong>Oliver Schilling</strong> (Eawag / Université de Bâle, Suisse), <strong>Hélène Budzinski</strong> (EPOC, Université de Bordeaux), <strong>Nicolas Massei</strong> (M2C, Université de Rouen Normandie), <strong>Konstantin Brenner</strong> (Laboratoire de Mathématiques J.-A. Dieudonné, Université Côte d’Azur), <strong>Jean Marçais</strong> · <strong>Arnaud Chaumot</strong> · <strong>Florentina Moatar</strong> (RiverLy, INRAE), <strong>Gilles Pinay</strong> (LEHNA, Université Claude Bernard Lyon 1), <strong>Sarah Leray</strong> · <strong>Hélène Fenet</strong> (HydroSciences Montpellier, CNRS / Université de Montpellier), <strong>Alexandre Gauvain</strong> (LMD, CNRS / Sorbonne Université), <strong>Étienne Bresciani</strong> (Universidad de O’Higgins, Chili), <strong>Susana Bernal</strong> · <strong>Josep Ramoneda</strong> (CEAB-CSIC, Blanes, Espagne), <strong>Matt Ross</strong> (Department of Ecosystem Science and Sustainability, Colorado State University, États-Unis).</p>
""",
    "en": """
<p class="collab-list"><strong>Luc Aquilina</strong> · <strong>Laurent Longuevergne</strong> · <strong>Tanguy Le Borgne</strong> · <strong>Thierry Labasque</strong> · <strong>Jean de Brémond d'Ars</strong> · <strong>Camille Bouchez</strong> · <strong>Hélène Hivert</strong> · <strong>Camille Vautier</strong> · <strong>Pierre Brigode</strong> (Géosciences Rennes, University of Rennes), <strong>Ronan Abhervé</strong> · <strong>Rémi Dupas</strong> (SAS, INRAE), <strong>Arnaud Blouin</strong> · <strong>Benoît Combemale</strong> (DIVERSE, IRISA, Inria), <strong>Alexandre Boisson</strong> · <strong>Anne Togola</strong> (BRGM), <strong>Clément Roques</strong> · <strong>Philip Brunner</strong> (CHYN, University of Neuchâtel, Switzerland), <strong>Florence Habets</strong> (Laboratoire de Géologie de l’ENS, ENS-PSL), <strong>Oliver Schilling</strong> (Eawag / University of Basel, Switzerland), <strong>Hélène Budzinski</strong> (EPOC, University of Bordeaux), <strong>Nicolas Massei</strong> (M2C, University of Rouen Normandy), <strong>Konstantin Brenner</strong> (Laboratoire de Mathématiques J.-A. Dieudonné, Université Côte d’Azur), <strong>Jean Marçais</strong> · <strong>Arnaud Chaumot</strong> · <strong>Florentina Moatar</strong> (RiverLy, INRAE), <strong>Gilles Pinay</strong> (LEHNA, Université Claude Bernard Lyon 1), <strong>Sarah Leray</strong> · <strong>Hélène Fenet</strong> (HydroSciences Montpellier, CNRS / University of Montpellier), <strong>Alexandre Gauvain</strong> (LMD, CNRS / Sorbonne University), <strong>Étienne Bresciani</strong> (Universidad de O’Higgins, Chile), <strong>Susana Bernal</strong> · <strong>Josep Ramoneda</strong> (CEAB-CSIC, Blanes, Spain), <strong>Matt Ross</strong> (Department of Ecosystem Science and Sustainability, Colorado State University, United States).</p>
""",
}


CV_COLLABORATIONS = {
    "fr": """
<div class="collaboration-grid">
  <article class="collaboration-group"><h3>Milieux fracturés et changement d’échelle</h3><p><strong>Philippe Davy, Olivier Bour, Brian Berkowitz et Jacques Bodin</strong> — réseaux de fractures, percolation, aquifères fracturés et karstiques.</p></article>
  <article class="collaboration-group"><h3>Calcul scientifique</h3><p><strong>Jocelyne Erhel, Géraldine Pichot, Anthony Beaudoin et Benoît Noetinger</strong> — méthodes numériques, calcul parallèle et changement d’échelle.</p></article>
  <article class="collaboration-group"><h3>Transport et réactivité</h3><p><strong>Alain Rapaport, Thierry Labasque, Jesús Carrera et Marco Dentz</strong> — transport réactif, dispersion, traceurs et temps de résidence.</p></article>
  <article class="collaboration-group"><h3>Âges et transport stochastique</h3><p><strong>Timothy R. Ginn, Arash Massoudieh et Daniel M. Tartakovsky</strong> — âge des eaux, inversion des traceurs et transport anormal.</p></article>
</div>
""",
    "en": """
<div class="collaboration-grid">
  <article class="collaboration-group"><h3>Fractured media and upscaling</h3><p><strong>Philippe Davy, Olivier Bour, Brian Berkowitz and Jacques Bodin</strong> — fracture networks, percolation, fractured and karst aquifers.</p></article>
  <article class="collaboration-group"><h3>Scientific computing</h3><p><strong>Jocelyne Erhel, Géraldine Pichot, Anthony Beaudoin and Benoît Noetinger</strong> — numerical methods, parallel computing and upscaling.</p></article>
  <article class="collaboration-group"><h3>Transport and reactivity</h3><p><strong>Alain Rapaport, Thierry Labasque, Jesús Carrera and Marco Dentz</strong> — reactive transport, dispersion, tracers and residence times.</p></article>
  <article class="collaboration-group"><h3>Groundwater age and stochastic transport</h3><p><strong>Timothy R. Ginn, Arash Massoudieh and Daniel M. Tartakovsky</strong> — groundwater age, tracer inversion and anomalous transport.</p></article>
</div>
""",
}


def update_home(page: BeautifulSoup, lang: str) -> None:
    replace_contents(page.find("main", id="main-content"), HOME[lang])
    description = page.find("meta", attrs={"name": "description"})
    description["content"] = (
        "Jean-Raynald de Dreuzy, président de l’ENS Rennes et directeur de recherche CNRS à Géosciences Rennes. Hydrogéologie, ressources en eau, qualité de l’eau et modélisation."
        if lang == "fr"
        else "Jean-Raynald de Dreuzy, President of ENS Rennes and CNRS Research Director at Géosciences Rennes. Hydrogeology, water resources, water quality and modelling."
    )
    for meta in page.find_all("meta"):
        if meta.get("property") == "og:description" or meta.get("name") == "twitter:description":
            meta["content"] = description["content"]


def update_research(page: BeautifulSoup, lang: str) -> None:
    main = page.find("main", id="main-content")
    for old in list(main.select(".deep-research-link, .discreet-gallery-link")):
        old.decompose()
    lead = main.select_one("p.lead")
    markup = (
        '<div class="deep-research-link"><div><strong>Cinq contributions scientifiques</strong><br/>Une sélection de résultats présentés par question, méthode et contribution.</div><a href="resultats-scientifiques.html">Explorer les résultats →</a></div>'
        if lang == "fr"
        else '<div class="deep-research-link"><div><strong>Five scientific contributions</strong><br/>A selection of results organised by question, method and contribution.</div><a href="scientific-results.html">Explore the results →</a></div>'
    )
    lead.insert_after(soup_fragment(markup).div)
    old_href = "logiciels.html#hydromodpy" if lang == "fr" else "software.html#hydromodpy"
    new_href = "hydromodpy.html"
    for anchor in main.find_all("a", href=old_href):
        anchor["href"] = new_href


def update_results_hub(page: BeautifulSoup, lang: str) -> None:
    lead = page.select_one("main p.lead")
    if lead:
        lead.string = (
            "Sélection de cinq questions qui ont structuré mes recherches. Chaque entrée présente la démarche suivie, les principaux résultats et les contributions associées."
            if lang == "fr"
            else "A selection of five questions that have shaped my research. Each entry presents the approach, main results and associated contributions."
        )
    note = page.select_one(".results-intro-note")
    if note:
        note.string = (
            "Sélection de cinq contributions structurantes. Chaque dossier relie une question scientifique, une méthode, un résultat et les publications associées."
            if lang == "fr"
            else "A selection of five structuring contributions. Each dossier links a scientific question, a method, a result and the associated publications."
        )
    results_section = page.select_one("main > section")
    if results_section and results_section.get("aria-label"):
        results_section["aria-label"] = "Sélection de résultats scientifiques" if lang == "fr" else "Selected scientific results"
    description = page.find("meta", attrs={"name": "description"})
    social_description = (
        "Sélection de questions, résultats et contributions scientifiques : aquifères peu profonds, temps de résidence, réactivité, modélisation et changement climatique."
        if lang == "fr"
        else "Selected scientific questions, results and contributions on shallow aquifers, residence times, reactivity, modelling and climate change."
    )
    if description:
        description["content"] = social_description
    for meta in page.find_all("meta"):
        if meta.get("property") == "og:description" or meta.get("name") == "twitter:description":
            meta["content"] = social_description
    update_result_links(page, lang)


def update_result_links(page: BeautifulSoup, lang: str) -> None:
    names = {"galerie-recherche.html", "research-figures.html"}
    for anchor in page.find_all("a", href=True):
        if anchor["href"].split("#", 1)[0] not in names:
            continue
        anchor["href"] = "science-societe.html#images-mediation" if lang == "fr" else "science-society.html#images-mediation"
        anchor.string = "Images et médiation →" if lang == "fr" else "Images and outreach →"


def update_projects(page: BeautifulSoup, lang: str) -> None:
    for style in page.head.find_all("style"):
        if "project-external-link" in style.get_text():
            style.decompose()
    main = page.find("main", id="main-content")
    replacements = (
        {"programme actuel 2024–2028": "programme actuel depuis 2024"}
        if lang == "fr"
        else {"current programme 2024–2028": "current programme since 2024"}
    )
    replace_text_nodes(main, replacements)
    current = heading_section(page, r"Autres projets actuels|Other current projects")
    if current:
        current.find("h2").string = (
            "Programmes structurants et autres projets actuels"
            if lang == "fr"
            else "Structuring programmes and other current projects"
        )
        if not current.find(id="iris-e"):
            markup = (
                '<div class="secondary-project" id="iris-e"><a class="project-external-link" href="https://iris-e.univ-rennes.fr/" rel="noopener" target="_blank"><strong>IRIS-E</strong></a> — programme en cours<br/><em>Interdisciplinary Research &amp; Innovative Solutions for Environmental transition</em><br/><strong>Responsabilité</strong> — co-responsable du WP2 « Recherches interdisciplinaires et co-construites »<br/>Programme de recherche et d’innovation de l’Université de Rennes destiné à soutenir des recherches interdisciplinaires construites avec les acteurs de la transition socio-environnementale.</div>'
                if lang == "fr"
                else '<div class="secondary-project" id="iris-e"><a class="project-external-link" href="https://iris-e.univ-rennes.fr/" rel="noopener" target="_blank"><strong>IRIS-E</strong></a> — ongoing programme<br/><em>Interdisciplinary Research &amp; Innovative Solutions for Environmental transition</em><br/><strong>Role</strong> — co-lead of WP2, “Interdisciplinary and co-designed research”<br/>The University of Rennes research and innovation programme supports interdisciplinary research co-designed with stakeholders in the socio-environmental transition.</div>'
            )
            current.find("h2").insert_after(soup_fragment(markup).div)


def update_team(page: BeautifulSoup, lang: str) -> None:
    main = page.find("main", id="main-content")
    main.find("h1").string = "Équipe" if lang == "fr" else "Team"
    lead = main.select_one("p.lead")
    if lead:
        lead.decompose()
    title = page.title
    title.string = ("Équipe" if lang == "fr" else "Team") + " — Jean-Raynald de Dreuzy"
    description = page.find("meta", attrs={"name": "description"})
    description["content"] = (
        "Doctorants, postdoctorants, ingénieurs, masters et anciens membres encadrés par Jean-Raynald de Dreuzy."
        if lang == "fr"
        else "PhD students, postdoctoral researchers, engineers, Master's students and former members supervised by Jean-Raynald de Dreuzy."
    )
    current_phd = heading_section(page, r"^Doctorants(?: en cours)?$|^(?:Current )?PhD students$")
    current_postdocs = heading_section(page, r"^Postdoctorants(?: en cours)?$|^(?:Current )?Postdoctoral researchers$")
    if current_phd:
        current_phd.find("h2").string = "Doctorants" if lang == "fr" else "PhD students"
    if current_postdocs:
        current_postdocs.find("h2").string = "Postdoctorants" if lang == "fr" else "Postdoctoral researchers"
        for badge in current_postdocs.select(".status-badge"):
            badge.decompose()
    collab = main.select_one(".collaboration-grid, .collab-list")
    if collab:
        replacement = soup_fragment(COLLABORATIONS[lang]).p
        collab.replace_with(replacement)
    former_phd = heading_section(page, r"Anciens doctorants|Archives doctorales|Former PhD students|Doctoral supervision archive")
    if former_phd:
        former_phd.find("h2").string = "Anciens doctorants" if lang == "fr" else "Former PhD students"
        details = former_phd.find("details", class_="data-details")
        if details:
            details.find("summary").decompose()
            details.unwrap()
    former_postdocs = heading_section(page, r"Anciens postdoctorants|Archives postdoctorales|Former postdoctoral researchers|Postdoctoral supervision archive")
    if former_postdocs:
        former_postdocs.find("h2").string = "Anciens postdoctorants" if lang == "fr" else "Former postdoctoral researchers"
        details = former_postdocs.find("details", class_="data-details")
        if details:
            details.find("summary").decompose()
            details.unwrap()
    for section in list(main.find_all("section", recursive=False)):
        if not section.get_text(" ", strip=True):
            section.decompose()


def add_recent_publications_host(page: BeautifulSoup, lang: str) -> None:
    main = page.find("main", id="main-content")
    if main.find(id="recent-publications"):
        return
    markup = (
        '<section class="section-block recent-publications" id="recent-publications"><h2>Dernières publications</h2><p class="small">Mise à jour automatiquement depuis la bibliographie complète.</p><div id="recent-publications-list"></div></section>'
        if lang == "fr"
        else '<section class="section-block recent-publications" id="recent-publications"><h2>Latest publications</h2><p class="small">Automatically updated from the full bibliography.</p><div id="recent-publications-list"></div></section>'
    )
    main.select_one("p.lead").insert_after(soup_fragment(markup).section)


def update_publications(page: BeautifulSoup, lang: str) -> None:
    add_recent_publications_host(page, lang)
    shallow = page.find("section", id="pub-shallow")
    doi = "https://doi.org/10.1016/j.ejrh.2026.103406"
    if shallow and not shallow.find("a", href=doi):
        markup = (
            '<div class="pub-entry" data-curated-id="pumping-tests-2026"><div class="pub-title"><a href="https://doi.org/10.1016/j.ejrh.2026.103406">A database of pumping tests in crystalline rocks: Lithostratigraphic controls on transmissivity and its log-normal distribution (Armorican Massif, France)</a></div><div class="pub-meta">A. Boisson et al. (2026) · <span class="smallcaps">Journal of Hydrology: Regional Studies</span>, 65, 103406</div></div>'
        )
        target = shallow.find("a", href="https://hess.copernicus.org/articles/30/5571/2026/")
        entry = soup_fragment(markup).div
        (target.find_parent("div", class_="pub-entry") if target else shallow.find("div", class_="pub-entry")).insert_before(entry)
    statuses = {
        "preparation": ("En préparation", "In preparation"),
        "submitted": ("Soumis", "Submitted"),
        "review": ("En révision", "In revision"),
    }
    for entry in page.select("main .pub-entry"):
        for badge in entry.select(".status-badge"):
            badge.decompose()
        text = entry.get_text(" ", strip=True).lower()
        state = None
        if "en préparation" in text or "in preparation" in text:
            state = "preparation"
        elif "en révision" in text or "in revision" in text:
            state = "review"
        elif "soumis" in text or "submitted" in text:
            state = "submitted"
        if state:
            meta = entry.select_one(".pub-meta")
            if meta:
                label = statuses[state][0 if lang == "fr" else 1]
                badge = soup_fragment(f'<span class="status-badge status-{state}">{label}</span>').span
                meta.insert(0, badge)


def update_publication_history(page: BeautifulSoup) -> None:
    heading = page.select_one("main > h1")
    if heading:
        heading.attrs.pop("style", None)
        heading["class"] = ["publication-history-title"]
    chart = page.select_one("main figure > img")
    if chart:
        chart.attrs.pop("style", None)
        chart["class"] = ["publication-history-chart"]


def update_software(page: BeautifulSoup, lang: str) -> None:
    hydro = page.find("section", id="hydromodpy")
    links = hydro.select_one(".software-links") if hydro else None
    if links and not links.find("a", href="hydromodpy.html"):
        anchor = soup_fragment(
            '<a href="hydromodpy.html">Page HydroModPy</a>' if lang == "fr" else '<a href="hydromodpy.html">HydroModPy page</a>'
        ).a
        links.insert(0, anchor)
    main = page.find("main", id="main-content")
    if not main.find(id="open-science"):
        markup = (
            '<section class="section-block" id="open-science"><h2>Données, codes et science ouverte</h2><p>Les logiciels sont complétés par des jeux de données, rapports et ressources destinés à rendre les méthodes et résultats réutilisables.</p><div class="finding-grid"><article><h3>Codes versionnés</h3><p><a href="https://github.com/HydroModPy/HydroModPy">HydroModPy sur GitHub</a> et distributions publiées sur PyPI.</p></article><article><h3>Données ouvertes</h3><p><a href="https://recherche.data.gouv.fr/fr/jeu-de-donnee/cartes-du-projet-rivages-normands-2100">Cartes et données de RIVAGES Normands 2100</a>.</p></article><article><h3>Rapports</h3><p><a href="assets/reports/Rapport_scientifique_final_CYDRE_2026_09.pdf">Rapport scientifique final CYDRE</a>, accessible directement sur le site.</p></article></div></section>'
            if lang == "fr"
            else '<section class="section-block" id="open-science"><h2>Data, code and open science</h2><p>The software is complemented by datasets, reports and resources designed to make methods and results reusable.</p><div class="finding-grid"><article><h3>Versioned code</h3><p><a href="https://github.com/HydroModPy/HydroModPy">HydroModPy on GitHub</a> and published PyPI distributions.</p></article><article><h3>Open data</h3><p><a href="https://recherche.data.gouv.fr/fr/jeu-de-donnee/cartes-du-projet-rivages-normands-2100">RIVAGES Normands 2100 maps and data</a>.</p></article><article><h3>Reports</h3><p><a href="../assets/reports/Rapport_scientifique_final_CYDRE_2026_09.pdf">CYDRE final scientific report</a>, directly available from this site.</p></article></div></section>'
        )
        main.append(soup_fragment(markup).section)


SCIENCE_IMAGES = {
    "fr": """
<section class="section-block" id="images-mediation"><h2>Images et médiation</h2><p class="lead">Six supports pour rendre visibles les circulations souterraines, les changements d’échelle et les liens entre modèles, terrain et territoires.</p><div class="outreach-gallery">
  <figure><a href="assets/maquette-nappes.jpg"><img alt="Maquette pédagogique d’une nappe souterraine" height="160" loading="lazy" src="assets/maquette-nappes.jpg" width="240"/></a><figcaption>Maquette de nappe : écoulements souterrains et propagation d’un traceur.</figcaption></figure>
  <figure><a href="assets/maquette-fractures.jpg"><img alt="Maquette pédagogique d’un milieu fracturé" height="177" loading="lazy" src="assets/maquette-fractures.jpg" width="145"/></a><figcaption>Maquette de milieu fracturé : chemins préférentiels dans un sous-sol complexe.</figcaption></figure>
  <figure><a href="recherche.html"><img alt="Calibration d’un modèle à partir du réseau hydrographique" height="540" loading="lazy" src="assets/figures/embedded/stream-calibration-illustration.webp" width="720"/></a><figcaption>Du réseau des rivières aux propriétés hydrauliques du sous-sol.</figcaption></figure>
  <figure><a href="resultat-temps-reactivite.html"><img alt="Stratification verticale de la réactivité" height="675" loading="lazy" src="assets/figures/embedded/reactivity-illustration.webp" width="900"/></a><figcaption>Réactivité stratifiée et élimination des nitrates dans les aquifères.</figcaption></figure>
  <figure><a href="resultat-climat-ressources.html"><img alt="Évolution des cours d’eau de tête sous changement climatique" height="540" loading="lazy" src="assets/figures/embedded/climate-streams-illustration.webp" width="720"/></a><figcaption>Transformation de la permanence des cours d’eau de tête sous changement climatique.</figcaption></figure>
  <figure><a href="resultat-milieux-fractures.html"><img alt="Réseaux de fractures et chenalisation des écoulements" height="1024" loading="lazy" src="assets/figures/fractured-media-channeling.webp" width="1536"/></a><figcaption>Connectivité des fractures et chenalisation des écoulements.</figcaption></figure>
</div></section>
""",
    "en": """
<section class="section-block" id="images-mediation"><h2>Images and outreach</h2><p class="lead">Six visual supports for making groundwater flow, changes of scale, and links between models, field observations and territories visible.</p><div class="outreach-gallery">
  <figure><a href="../assets/maquette-nappes.jpg"><img alt="Teaching model of a groundwater table" height="160" loading="lazy" src="../assets/maquette-nappes.jpg" width="240"/></a><figcaption>Groundwater model: subsurface flow and tracer propagation.</figcaption></figure>
  <figure><a href="../assets/maquette-fractures.jpg"><img alt="Teaching model of a fractured medium" height="177" loading="lazy" src="../assets/maquette-fractures.jpg" width="145"/></a><figcaption>Fractured-medium model: preferential pathways through a complex subsurface.</figcaption></figure>
  <figure><a href="research.html"><img alt="Model calibration using the stream network" height="540" loading="lazy" src="../assets/figures/embedded/stream-calibration-illustration.webp" width="720"/></a><figcaption>From stream networks to subsurface hydraulic properties.</figcaption></figure>
  <figure><a href="result-transit-reactivity.html"><img alt="Vertical stratification of aquifer reactivity" height="675" loading="lazy" src="../assets/figures/embedded/reactivity-illustration.webp" width="900"/></a><figcaption>Stratified reactivity and nitrate removal in aquifers.</figcaption></figure>
  <figure><a href="result-climate-water-resources.html"><img alt="Headwater streams under climate change" height="540" loading="lazy" src="../assets/figures/embedded/climate-streams-illustration.webp" width="720"/></a><figcaption>Changing permanence of headwater streams under climate change.</figcaption></figure>
  <figure><a href="result-fractured-media.html"><img alt="Fracture networks and flow channelling" height="1024" loading="lazy" src="../assets/figures/fractured-media-channeling.webp" width="1536"/></a><figcaption>Fracture connectivity and flow channelling.</figcaption></figure>
</div></section>
""",
}


def update_science_society(page: BeautifulSoup, lang: str) -> None:
    for style in page.head.find_all("style"):
        if "outreach-gallery" in style.get_text():
            style.decompose()
    main = page.find("main", id="main-content")
    replace_text_nodes(
        main,
        {
            "2019–2028": "2019–",
            "2022–2024": "2023–2026",
            "programme 2024–2028": "programme actuel depuis 2024",
            "current programme 2024–2028": "current programme since 2024",
        },
    )
    current = main.find("section", id="recent-activities")
    archive = main.find("section", id="earlier-activities")
    if current:
        current.find("h2").string = "À la une" if lang == "fr" else "Highlights"
        if not current.find(attrs={"data-curated-id": "giec-water-2026"}):
            first_h3 = current.find("h3")
            entry = soup_fragment(
                '<div class="pub-entry" data-curated-id="giec-water-2026"><div class="meta-line">2026 · GIEC Pays de la Loire</div><div class="pub-title"><a href="https://insu.hal.science/insu-05461869/document" rel="noopener" target="_blank">L’avenir de la ressource en eau face aux changements climatiques dans les Pays de la Loire</a></div><div class="pub-meta">Rapport collectif, volume 2, 88 pages · expertise scientifique sur la disponibilité, la qualité et les usages de l’eau.</div></div>'
                if lang == "fr"
                else '<div class="pub-entry" data-curated-id="giec-water-2026"><div class="meta-line">2026 · Pays de la Loire regional climate panel</div><div class="pub-title"><a href="https://insu.hal.science/insu-05461869/document" rel="noopener" target="_blank">L’avenir de la ressource en eau face aux changements climatiques dans les Pays de la Loire</a></div><div class="pub-meta">Collective report, volume 2, 88 pages · scientific assessment of water availability, quality and uses.</div></div>'
            ).div
            first_h3.insert_after(entry)
        territory_h3 = current.find("h3", string=re.compile(r"Recherche, territoires|Research, territories", re.IGNORECASE))
        if territory_h3 and not current.find(id="territory-links"):
            for sibling in list(territory_h3.next_siblings):
                sibling.extract()
            markup = (
                '<div class="finding-grid" id="territory-links"><article><h3>Ressources et territoires</h3><p>Chaire Eaux &amp; Territoires, EAUX 2050, RIVIÈRES 2070 et CYDRE.</p><a href="projets.html#water-territories">Voir les projets →</a></article><article><h3>Risques côtiers</h3><p>De RIVAGES Normands 2100 à ARCHANGE : remontées de nappe, salinisation et adaptation.</p><a href="risques-cotiers.html">Voir le dossier →</a></article><article><h3>Empreinte et observation</h3><p>OneWater, Empreinte Eau et Eau Sentinelle au sein des socio-hydrosystèmes.</p><a href="projets.html#onewater">Voir dans les projets →</a></article></div>'
                if lang == "fr"
                else '<div class="finding-grid" id="territory-links"><article><h3>Water and territories</h3><p>Water &amp; Territories Chair, EAUX 2050, RIVIÈRES 2070 and CYDRE.</p><a href="projects.html#water-territories">View projects →</a></article><article><h3>Coastal risks</h3><p>From RIVAGES Normands 2100 to ARCHANGE: groundwater rise, salinisation and adaptation.</p><a href="coastal-risks.html">View the dossier →</a></article><article><h3>Footprint and observation</h3><p>OneWater, Water Footprint and Sentinel Water across socio-hydrological systems.</p><a href="projects.html#onewater">View within projects →</a></article></div>'
            )
            territory_h3.insert_after(soup_fragment(markup).div)
    image_section = soup_fragment(SCIENCE_IMAGES[lang]).section
    existing_images = main.find(id="images-mediation")
    if existing_images:
        existing_images.replace_with(image_section)
    elif archive:
        archive.insert_before(image_section)
    else:
        main.append(image_section)
    if archive:
        archive.find("h2").string = "Archives" if lang == "fr" else "Archive"
        if not archive.find("details", class_="data-details"):
            details = soup_fragment(
                '<details class="data-details"><summary>Afficher les activités antérieures</summary></details>'
                if lang == "fr"
                else '<details class="data-details"><summary>Show earlier activities</summary></details>'
            ).details
            for child in list(archive.contents):
                if isinstance(child, Tag) and child.name == "h2":
                    continue
                details.append(child.extract())
            archive.append(details)


def update_cv(page: BeautifulSoup, lang: str) -> None:
    main = page.find("main", id="main-content")
    for row in list(main.select(".timeline-row")):
        if "Sciences pour l’Environnement" in row.get_text() or "Environmental Sciences Department" in row.get_text():
            row.decompose()
    for paragraph in list(main.find_all("p")):
        if "Sciences pour l’Environnement" in paragraph.get_text() or "Environmental Sciences Department" in paragraph.get_text():
            paragraph.decompose()
    current = heading_section(page, r"Positions principales|Current positions")
    if current:
        for row in current.select(".timeline-row"):
            if "2013" in row.select_one(".timeline-year").get_text():
                cells = row.find_all("div", recursive=False)
                replace_contents(
                    cells[1],
                    "<strong>Directeur de recherche, CNRS</strong> — Université de Rennes"
                    if lang == "fr"
                    else "<strong>Research Director, CNRS</strong> — University of Rennes",
                )
    structuring = heading_section(page, r"Responsabilités et structuration scientifique|Responsibilities and research structuring")
    if structuring:
        structuring.find("h2").string = (
            "Responsabilités et structuration scientifique — sélection"
            if lang == "fr"
            else "Responsibilities and research structuring — selected"
        )
        for row in structuring.select(".timeline-row"):
            if "2017–2021" in row.get_text():
                cells = row.find_all("div", recursive=False)
                replace_contents(
                    cells[1],
                    'Direction de l’OSUR, aujourd’hui <a href="https://oseren.univ-rennes.fr/">OSERen</a> : plateformes, observatoires, programmes interdisciplinaires et partenariats territoriaux.'
                    if lang == "fr"
                    else 'Leadership of OSUR, now <a href="https://oseren.univ-rennes.fr/">OSERen</a>: platforms, observatories, interdisciplinary programmes and partnerships with regional stakeholders.',
                )
        roles = [
            ("2018–2024", "Présidence du conseil de l’Observatoire Ecce-Terra, Sorbonne Université." if lang == "fr" else "Chair of the Ecce-Terra Observatory Council, Sorbonne University."),
            ("2021–2024", "Membre de la commission scientifique spécialisée STEA de l’INRAE." if lang == "fr" else "Member of INRAE’s specialised STEA scientific commission."),
            ("2017–2018", "Vice-présidence d’un comité d’évaluation de l’Agence nationale de la recherche." if lang == "fr" else "Vice-Chair of a French National Research Agency evaluation panel."),
            ("2018–2024", "Membre du comité permanent de Computational Methods in Water Resources." if lang == "fr" else "Member of the Standing Committee for Computational Methods in Water Resources."),
        ]
        for index, (year, text) in enumerate(roles, start=1):
            if structuring.find(attrs={"data-curated-role": str(index)}):
                continue
            append_fragment(structuring, f'<div class="timeline-row" data-curated-role="{index}"><div class="timeline-year">{year}</div><div>{text}</div></div>')
    previous = heading_section(page, r"Responsabilités antérieures|Selected previous responsibilities")
    if previous:
        previous.decompose()
    download = main.select_one(".download-cv")
    if download and not download.select_one(".cv-updated"):
        label = "Mis à jour le 20 septembre 2026" if lang == "fr" else "Updated 20 September 2026"
        append_fragment(download, f'<span class="cv-updated">{label}</span>')
    collab_section = heading_section(page, r"Collaborations scientifiques antérieures|Past scientific collaborations")
    if collab_section:
        old = collab_section.select_one(".collab-list")
        if old:
            old.replace_with(soup_fragment(CV_COLLABORATIONS[lang]).div)
    page.title.string = "CV — Jean-Raynald de Dreuzy"
    description = page.find("meta", attrs={"name": "description"})
    description["content"] = (
        "CV de Jean-Raynald de Dreuzy : président de l’ENS Rennes, directeur de recherche CNRS, responsabilités scientifiques, projets, publications et encadrement."
        if lang == "fr"
        else "CV of Jean-Raynald de Dreuzy: President of ENS Rennes, CNRS Research Director, scientific responsibilities, projects, publications and supervision."
    )
    for meta in page.find_all("meta"):
        if meta.get("property") == "og:description" or meta.get("name") == "twitter:description":
            meta["content"] = description["content"]


def transform(path: Path, lang: str) -> str:
    page = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    name = path.name
    if name == "index.html":
        update_home(page, lang)
    elif name in {"recherche.html", "research.html"}:
        update_research(page, lang)
    elif name in {"resultats-scientifiques.html", "scientific-results.html"}:
        update_results_hub(page, lang)
    elif name in {"projets.html", "projects.html"}:
        update_projects(page, lang)
    elif name in {"equipe.html", "team.html"}:
        update_team(page, lang)
    elif name == "publications.html":
        update_publications(page, lang)
    elif name in {"publications-au-fil-du-temps.html", "publications-over-time.html"}:
        update_publication_history(page)
    elif name in {"logiciels.html", "software.html"}:
        update_software(page, lang)
    elif name in {"science-societe.html", "science-society.html"}:
        update_science_society(page, lang)
    elif name == "cv.html":
        update_cv(page, lang)
    if name.startswith("resultat-") or name.startswith("result-"):
        update_result_links(page, lang)
    return str(page)


PAGES = [
    ("index.html", "fr"),
    ("en/index.html", "en"),
    ("recherche.html", "fr"),
    ("en/research.html", "en"),
    ("resultats-scientifiques.html", "fr"),
    ("en/scientific-results.html", "en"),
    ("projets.html", "fr"),
    ("en/projects.html", "en"),
    ("equipe.html", "fr"),
    ("en/team.html", "en"),
    ("publications.html", "fr"),
    ("en/publications.html", "en"),
    ("publications-au-fil-du-temps.html", "fr"),
    ("en/publications-over-time.html", "en"),
    ("logiciels.html", "fr"),
    ("en/software.html", "en"),
    ("science-societe.html", "fr"),
    ("en/science-society.html", "en"),
    ("cv.html", "fr"),
    ("en/cv.html", "en"),
    ("resultat-rivieres-sous-sol.html", "fr"),
    ("resultat-temps-reactivite.html", "fr"),
    ("resultat-modeles-europe.html", "fr"),
    ("resultat-climat-ressources.html", "fr"),
    ("resultat-milieux-fractures.html", "fr"),
    ("en/result-streams-subsurface.html", "en"),
    ("en/result-transit-reactivity.html", "en"),
    ("en/result-models-europe.html", "en"),
    ("en/result-climate-water-resources.html", "en"),
    ("en/result-fractured-media.html", "en"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when curated pages are stale")
    args = parser.parse_args()
    stale: list[str] = []
    for relative, lang in PAGES:
        path = ROOT / relative
        source = path.read_text(encoding="utf-8")
        output = transform(path, lang)
        if output == source:
            continue
        stale.append(relative)
        if not args.check:
            path.write_text(output, encoding="utf-8")
    if args.check and stale:
        print("Curated content is stale:", file=sys.stderr)
        for relative in stale:
            print(f"- {relative}", file=sys.stderr)
        return 1
    print(f"Curated content {'checked' if args.check else 'built'}: {len(stale)} file(s) changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
