#!/usr/bin/env python3
"""Generate the downloadable French CV used by the website."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "cv" / "CV_Jean-Raynald_de_Dreuzy_2026.pdf"
NAVY = colors.HexColor("#17324A")
BLUE = colors.HexColor("#0056B3")
MUTED = colors.HexColor("#526975")
LINE = colors.HexColor("#D9E2E8")
SOFT = colors.HexColor("#F3F7F9")


def register_fonts() -> None:
    paths = {
        "DejaVu": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVu-Bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVu-Serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "DejaVu-Serif-Bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    }
    for name, path in paths.items():
        pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu", boldItalic="DejaVu-Bold")
    pdfmetrics.registerFontFamily("DejaVu-Serif", normal="DejaVu-Serif", bold="DejaVu-Serif-Bold", italic="DejaVu-Serif", boldItalic="DejaVu-Serif-Bold")


def page_chrome(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("DejaVu", 7.8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9.2 * mm, "Jean-Raynald de Dreuzy · CV synthétique · septembre 2026")
    canvas.drawRightString(width - 18 * mm, 9.2 * mm, f"{doc.page}")
    canvas.restoreState()


def bullet(text: str, styles, level: int = 0) -> Paragraph:
    return Paragraph(text, styles["CvBullet" if level == 0 else "CvSubBullet"], bulletText="•")


def timeline(rows: list[tuple[str, str]], styles) -> Table:
    data = [[Paragraph(year, styles["Year"]), Paragraph(text, styles["Body"])] for year, text in rows]
    table = Table(data, colWidths=[31 * mm, 139 * mm], hAlign="LEFT", repeatRows=0)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, -1), 4 * mm),
        ("RIGHTPADDING", (1, 0), (1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2 * mm),
        ("LINEBELOW", (0, 0), (-1, -2), 0.35, LINE),
    ]))
    return table


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "Name", fontName="DejaVu-Serif-Bold", fontSize=25, leading=29,
        textColor=NAVY, spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        "Role", fontName="DejaVu", fontSize=11.2, leading=15,
        textColor=MUTED, spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        "Contact", fontName="DejaVu", fontSize=8.4, leading=12,
        textColor=NAVY, spaceAfter=6 * mm,
    ))
    styles.add(ParagraphStyle(
        "Section", fontName="DejaVu-Serif-Bold", fontSize=15, leading=18,
        textColor=NAVY, spaceBefore=5 * mm, spaceAfter=2.3 * mm,
        borderWidth=0, borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        "Subsection", fontName="DejaVu-Bold", fontSize=10.2, leading=13,
        textColor=NAVY, spaceBefore=3 * mm, spaceAfter=1 * mm,
    ))
    styles.add(ParagraphStyle(
        "Body", fontName="DejaVu", fontSize=8.7, leading=12.2,
        textColor=colors.HexColor("#2F3E49"), spaceAfter=1.5 * mm,
    ))
    styles.add(ParagraphStyle(
        "Lead", fontName="DejaVu", fontSize=10.2, leading=14.2,
        textColor=colors.HexColor("#40525E"), spaceAfter=4 * mm,
    ))
    styles.add(ParagraphStyle(
        "CvBullet", fontName="DejaVu", fontSize=8.6, leading=12,
        leftIndent=4.5 * mm, firstLineIndent=-3.2 * mm, bulletIndent=0,
        textColor=colors.HexColor("#2F3E49"), spaceAfter=1.2 * mm,
    ))
    styles.add(ParagraphStyle(
        "CvSubBullet", fontName="DejaVu", fontSize=8.2, leading=11.5,
        leftIndent=8 * mm, firstLineIndent=-3.2 * mm, bulletIndent=3.5 * mm,
        textColor=colors.HexColor("#40525E"), spaceAfter=1 * mm,
    ))
    styles.add(ParagraphStyle(
        "Year", fontName="DejaVu-Bold", fontSize=8.4, leading=12,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        "Kicker", fontName="DejaVu-Bold", fontSize=7.4, leading=10,
        textColor=colors.HexColor("#497A9C"), spaceBefore=1.5 * mm, spaceAfter=.5 * mm,
    ))
    styles.add(ParagraphStyle(
        "Small", fontName="DejaVu", fontSize=7.7, leading=10.5,
        textColor=MUTED,
    ))
    return styles


def section_title(text: str, styles) -> KeepTogether:
    rule = Table([[""]], colWidths=[170 * mm], rowHeights=[0.55 * mm])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LINE)]))
    return KeepTogether([Spacer(1, 2.5 * mm), rule, Paragraph(text, styles["Section"])])


def main() -> None:
    register_fonts()
    styles = build_styles()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=17 * mm, bottomMargin=19 * mm,
        title="CV — Jean-Raynald de Dreuzy",
        author="Jean-Raynald de Dreuzy",
        subject="Curriculum vitae synthétique — septembre 2026",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id="cv", frames=[frame], onPage=page_chrome))

    story = []
    story.append(Paragraph("Jean-Raynald de Dreuzy", styles["Name"]))
    story.append(Paragraph("Hydrogéologue · Directeur de recherche CNRS · Président de l’École normale supérieure de Rennes", styles["Role"]))
    story.append(Paragraph(
        '<link href="mailto:jean-raynald.de-dreuzy@univ-rennes.fr" color="#0056B3">jean-raynald.de-dreuzy@univ-rennes.fr</link> &nbsp;·&nbsp; '
        '<link href="https://dreuzy.github.io/" color="#0056B3">dreuzy.github.io</link> &nbsp;·&nbsp; '
        '<link href="https://orcid.org/0000-0003-2993-2015" color="#0056B3">ORCID 0000-0003-2993-2015</link> &nbsp;·&nbsp; '
        '<link href="https://hal.science/search/index/?q=%22Jean-Raynald%20de%20Dreuzy%22" color="#0056B3">HAL</link>',
        styles["Contact"],
    ))
    story.append(Paragraph(
        "Mes recherches portent sur le fonctionnement des aquifères peu profonds et des bassins versants de tête, "
        "les temps de transfert et la qualité de l’eau, ainsi que l’évolution des ressources sous changement climatique. "
        "Elles associent observations, traceurs, modélisation hydrogéologique, méthodes numériques et co-construction avec les territoires.",
        styles["Lead"],
    ))

    story.append(section_title("Positions actuelles", styles))
    story.append(timeline([
        ("Depuis 2026", "<b>Président</b> — École normale supérieure de Rennes"),
        ("Depuis 2013", "<b>Directeur de recherche CNRS</b> — Géosciences Rennes, Université de Rennes"),
    ], styles))

    story.append(section_title("Axes scientifiques", styles))
    for item in [
        "Aquifères peu profonds, bassins versants de tête et échanges surface–souterrain.",
        "Temps de résidence, transferts de nitrates, réactivité et résilience de la qualité de l’eau.",
        "Effets du changement climatique sur les ressources, les faibles débits et les risques côtiers.",
        "Modèles multi-fidélité, méthodes numériques et chaînes reproductibles de simulation.",
        "Interface entre recherche, observation, gestion de l’eau et décision territoriale.",
    ]:
        story.append(bullet(item, styles))

    story.append(section_title("Responsabilités scientifiques actuelles", styles))
    for item in [
        "<b>OneWater — Eau Bien Commun</b> : co-responsable du défi « Empreinte Eau » et d’un projet ciblé du PEPR national.",
        "<b>IRIS-E</b> : co-responsable du WP2 « Recherches interdisciplinaires et co-construites ».",
        "<b>Chaire Eaux & Territoires</b> : co-titulaire avec Luc Aquilina, Fondation Université de Rennes.",
        "<b>ANDRA</b> : membre du conseil scientifique depuis 2025.",
        "<b>OREME</b> : président du conseil depuis 2025.",
        "<b>GIEC des Pays de la Loire</b> : membre depuis 2024.",
    ]:
        story.append(bullet(item, styles))

    story.append(PageBreak())
    story.append(Paragraph("Parcours et structuration scientifique", styles["Name"]))
    story.append(section_title("Positions antérieures", styles))
    story.append(timeline([
        ("2021–2026", "Vice-président Recherche — École normale supérieure de Rennes"),
        ("2017–2021", "Directeur de l’Observatoire des Sciences de l’Univers de Rennes (OSUR)"),
        ("2013–2016", "Chercheur associé à Inria, Rennes"),
        ("2011–2013", "Mobilité Marie Curie — IDAEA-CSIC / Universitat Politècnica de Catalunya, Barcelone"),
        ("2001–2010", "Chargé de recherche CNRS — Géosciences Rennes"),
        ("2000–2001", "Postdoctorat — Institut Weizmann, Israël"),
    ], styles))

    story.append(section_title("Formation", styles))
    story.append(timeline([
        ("2008", "Habilitation à diriger des recherches — modélisation des écoulements et du transport dans les milieux fortement hétérogènes et fracturés, Université de Rennes 1"),
        ("1996–1999", "Doctorat — Géosciences Rennes, CNRS / Université de Rennes 1"),
        ("1995", "DEA d’Hydrologie et d’Hydrogéologie — Université Paris VI"),
        ("1992–1994", "École polytechnique"),
    ], styles))

    story.append(section_title("Structuration de la recherche", styles))
    for year, text in [
        ("2022–2024", "Création et direction du département Sciences pour l’Environnement de l’ENS Rennes."),
        ("Depuis 2021", "Contribution au montage de OneWater et d’IRIS-E, avec un accent sur l’interdisciplinarité et la co-construction."),
        ("2018–2021", "Portage du CPER GLAZ Environnement et développement d’une plateforme régionale d’observation."),
        ("2017–2021", "Direction de l’OSUR : plateformes, observatoires, projets interdisciplinaires et partenariats territoriaux."),
        ("2014–2017", "Création et animation de RISC-E et de l’Observatoire Virtuel de l’Environnement."),
        ("2013–2016", "Responsabilité de l’équipe EAU de Géosciences Rennes."),
    ]:
        story.append(bullet(f"<b>{year}</b> — {text}", styles))

    story.append(PageBreak())
    story.append(Paragraph("Principaux contrats de recherche", styles["Name"]))
    story.append(Paragraph(
        'Détails, partenaires et liens officiels : <link href="https://dreuzy.github.io/projets.html" color="#0056B3">dreuzy.github.io/projets.html</link>',
        styles["Lead"],
    ))
    story.append(timeline([
        ("2026–", "<b>FutureFlow</b> — ANR PRCI France–Suisse, ANR-25-CE01-2963. Approche multi-fidélité pour quantifier la contribution des eaux souterraines aux bassins versants de tête. Coordination avec Clément Roques."),
        ("2023–", "<b>OneWater — PC4 OWMS</b> — ANR-22-PEXO-0005. Empreinte eau et observation multidimensionnelle des hydrosystèmes ; programme OneWater lancé en 2022."),
        ("2019–", "<b>Chaire Eaux & Territoires</b> — Fondation Université de Rennes. Programme actuel 2024–2028 ; ressources, usages et adaptation territoriale."),
        ("2025–", "<b>ARCHANGE</b> — remontée de nappe et intrusion saline en baie du Mont-Saint-Michel, dans le prolongement de RIVAGES Normands 2100."),
        ("2024–", "<b>NIRECAS</b> — MSCA-PF 101150996. Capacité de récupération vis-à-vis des nitrates sur 200 sites pilotes du Massif armoricain."),
        ("2019–2025", "<b>RIVAGES Normands 2100</b> — risques hydrogéologiques littoraux, recherche transdisciplinaire et adaptation des territoires."),
        ("2019–2026", "<b>EAUX 2050 / RIVIÈRES 2070 / CYDRE</b> — projections climatiques, dialogue territorial et prévision saisonnière sur 98 bassins."),
        ("2014–2019", "<b>AquiFR-BZH</b> — évaluation régionale des ressources dans les aquifères de socle."),
        ("2011–2013", "<b>MUIGECCOS</b> — Marie Curie IEF 251710, processus couplés et stockage géologique du CO₂."),
        ("2007–2010", "<b>MOHINI</b> — ANR-07-VULN-0008, ressources en eau et vulnérabilité des aquifères de socle."),
    ], styles))

    story.append(section_title("Encadrement et logiciels", styles))
    story.append(bullet("Encadrement et co-encadrement de doctorants, postdoctorants, Masters et stagiaires en hydrogéologie, hydrologie, qualité de l’eau et modélisation.", styles))
    story.append(bullet('<b>HydroModPy</b> — boîte à outils Python pour déployer des modèles d’aquifères peu profonds à l’échelle des bassins versants.', styles))
    story.append(bullet('<b>PyAges</b> — boîte à outils extensible pour l’interprétation des âges des eaux souterraines par modèles à paramètres groupés.', styles))

    story.append(PageBreak())
    story.append(Paragraph("Activités scientifiques et publications", styles["Name"]))
    story.append(section_title("Activités éditoriales et animation", styles))
    for item in [
        "<b>Hydrogeology Journal</b>, 2006–2011 — éditeur associé.",
        "<b>Journal of Hydrology</b>, 2013–2018 — éditeur associé ; co-éditeur d’un numéro spécial sur les temps de résidence en 2016.",
        "<b>Computational Methods in Water Resources</b>, 2018–2024 — membre du comité permanent.",
        "<b>CMWR 2018, Saint-Malo</b> — co-organisateur de la XXIIe conférence internationale avec Jocelyne Erhel et Tanguy Le Borgne.",
        "Participation à des conseils et comités d’évaluation nationaux en environnement, hydrologie et sciences de la Terre.",
    ]:
        story.append(bullet(item, styles))

    story.append(section_title("Publications — repères", styles))
    story.append(Paragraph(
        "114 articles publiés référencés dans la bibliographie du site, auxquels s’ajoutent actes, chapitres, rapports et communications. "
        "Les travaux couvrent les réseaux de fractures, le transport en milieux hétérogènes, les temps de résidence, la réactivité des aquifères, "
        "les échanges nappe–rivière et l’adaptation des ressources en eau.", styles["Body"],
    ))
    for item in [
        "Le Mesnil et al. (2026), <i>Rivages Normands 2100: transdisciplinary co-constructed knowledge for land-use adaptation to groundwater rise along Normandy coastline</i>, Sustainability Science.",
        "Gauvain et al. (2026), <i>Technical note: HydroModPy (v1.0)</i>, Hydrology and Earth System Sciences.",
        "Abhervé et al. (2023), <i>Calibration of groundwater seepage against the spatial distribution of the stream network</i>, Hydrology and Earth System Sciences — Highlight paper.",
        "Kolbe et al. (2019), <i>Stratification of reactivity determines nitrate removal in groundwater</i>, PNAS.",
        "Vergnes et al. (2020), <i>The AquiFR hydrometeorological modelling platform</i>, Hydrology and Earth System Sciences.",
        "Pichot, Erhel & de Dreuzy (2012), <i>A Generalized Mixed Hybrid Mortar Method for Solving Flow in Stochastic Discrete Fracture Networks</i>, SIAM Journal on Scientific Computing.",
    ]:
        story.append(bullet(item, styles))

    story.append(section_title("Liens", styles))
    links = [
        ("Publications sélectionnées", "https://dreuzy.github.io/publications.html"),
        ("Bibliographie complète", "https://dreuzy.github.io/bibliographie.html"),
        ("Équipe et encadrements", "https://dreuzy.github.io/equipe.html"),
        ("Projets et contrats", "https://dreuzy.github.io/projets.html"),
        ("Logiciels", "https://dreuzy.github.io/logiciels.html"),
    ]
    story.append(Paragraph(" &nbsp;·&nbsp; ".join(f'<link href="{url}" color="#0056B3">{label}</link>' for label, url in links), styles["Body"]))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Dernière mise à jour : 20 septembre 2026", styles["Small"]))

    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
