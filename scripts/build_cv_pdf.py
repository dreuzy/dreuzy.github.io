#!/usr/bin/env python3
"""Build a conventional scientific CV, with restrained typography and layout."""
from __future__ import annotations
import argparse
import json
import os
import tempfile
from pathlib import Path
import matplotlib
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, KeepTogether, PageTemplate, Paragraph, Spacer, Table, TableStyle

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/"site-config.json").read_text(encoding="utf-8"))
OUT=ROOT/CONFIG["cv"]["pdf"]
UPDATED=CONFIG["cv"]["updated"]
PUBLICATION_COUNT=int(CONFIG["cv"]["publication_count"])
rl_config.invariant=True
INK=colors.HexColor("#222222")
MUTED=colors.HexColor("#555555")
HAIRLINE=colors.HexColor("#B9BEC2")
PAGE_WIDTH,PAGE_HEIGHT=A4
BODY_WIDTH=166*mm

def register_fonts():
    base=Path(matplotlib.get_data_path())/"fonts"/"ttf"
    for name,file in [("DejaVu","DejaVuSans.ttf"),("DejaVu-Bold","DejaVuSans-Bold.ttf"),("DejaVu-Serif","DejaVuSerif.ttf"),("DejaVu-Serif-Bold","DejaVuSerif-Bold.ttf")]:
        pdfmetrics.registerFont(TTFont(name,str(base/file)))
    pdfmetrics.registerFontFamily("DejaVu",normal="DejaVu",bold="DejaVu-Bold",italic="DejaVu",boldItalic="DejaVu-Bold")

def styles():
    s=getSampleStyleSheet()
    for name,kw in [
        ("CVName",dict(fontName="DejaVu-Bold",fontSize=17.6,leading=22,textColor=INK,spaceAfter=4)),
        ("CVPosition",dict(fontName="DejaVu",fontSize=9.1,leading=13,textColor=INK,spaceAfter=3)),
        ("CVContact",dict(fontName="DejaVu",fontSize=8.3,leading=11.4,textColor=MUTED,spaceAfter=12)),
        ("CVSection",dict(fontName="DejaVu-Bold",fontSize=10.7,leading=14.7,textColor=INK,spaceBefore=8,spaceAfter=5,keepWithNext=True)),
        ("CVText",dict(fontName="DejaVu",fontSize=8.65,leading=12.5,textColor=INK,spaceAfter=4)),
        ("CVSmall",dict(fontName="DejaVu",fontSize=8.2,leading=11.7,textColor=MUTED,spaceAfter=3)),
        ("CVDate",dict(fontName="DejaVu",fontSize=8.45,leading=12.5,textColor=MUTED)),
    ]: s.add(ParagraphStyle(name,**kw))
    return s

def link(label,url):
    return f'<link href="{url}" color="#294C66">{label}</link>'

def section(label,s):
    line=Table([[""]],colWidths=[BODY_WIDTH],rowHeights=[0.25*mm])
    line.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),HAIRLINE),("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    return KeepTogether([Paragraph(label,s["CVSection"]),line,Spacer(1,4)])

def para(t,s): return Paragraph(t,s["CVText"])

def role_table(items,s,date_w=32*mm):
    t=Table([[Paragraph(date,s["CVDate"]),para(txt,s)] for date,txt in items],colWidths=[date_w,BODY_WIDTH-date_w],hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(0,-1),7),("RIGHTPADDING",(1,0),(1,-1),0),("TOPPADDING",(0,0),(-1,-1),1),("BOTTOMPADDING",(0,0),(-1,-1),4.4)]))
    return t

def bullets(items,s): return [para("&#8226; "+x,s) for x in items]

def footer(canvas,doc):
    canvas.saveState()
    canvas.setFillColor(MUTED);canvas.setFont("DejaVu",7.4)
    canvas.drawString(22*mm,13*mm,"Jean-Raynald de Dreuzy")
    canvas.drawRightString(PAGE_WIDTH-22*mm,13*mm,str(doc.page))
    canvas.restoreState()

def main():
    p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");args=p.parse_args()
    register_fonts();s=styles();OUT.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix="cv-academic-",suffix=".pdf",dir=OUT.parent);os.close(fd);tmp=Path(name)
    doc=BaseDocTemplate(str(tmp),pagesize=A4,leftMargin=22*mm,rightMargin=22*mm,topMargin=20*mm,bottomMargin=20*mm,title="Curriculum vitae - Jean-Raynald de Dreuzy",author="Jean-Raynald de Dreuzy",subject=f"Curriculum vitae scientifique, actualisé le {UPDATED}")
    frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id="main")
    doc.addPageTemplates(PageTemplate(id="academic",frames=[frame],onPage=footer))
    story=[
        Paragraph("Jean-Raynald de Dreuzy",s["CVName"]),
        Paragraph("Directeur de recherche CNRS, Géosciences Rennes (UMR 6118) · Président de l’École normale supérieure de Rennes",s["CVPosition"]),
        Paragraph(link("jean-raynald.de-dreuzy@ens-rennes.fr","mailto:jean-raynald.de-dreuzy@ens-rennes.fr")+" &nbsp; | &nbsp; "+link("Site personnel","https://dreuzy.github.io/")+" &nbsp; | &nbsp; "+link("ORCID","https://orcid.org/0000-0003-2993-2015")+" &nbsp; | &nbsp; "+link("HAL","https://hal.science/search/index/?q=%22Jean-Raynald%20de%20Dreuzy%22"),s["CVContact"]),
        section("Fonctions et parcours",s),
        role_table([
            ("Depuis 2026","Président de l’École normale supérieure de Rennes."),
            ("Depuis 2013","Directeur de recherche CNRS, Géosciences Rennes, Université de Rennes."),
            ("2021–2026","Vice-président Recherche, ENS Rennes."),
            ("2017–2021","Directeur de l’Observatoire des Sciences de l’Univers de Rennes (OSUR, aujourd’hui OSERen)."),
            ("2013–2016","Chercheur associé à Inria, Rennes."),
            ("2011–2013","Mobilité Marie Curie, IDAEA-CSIC / Universitat Politècnica de Catalunya, Barcelone."),
            ("2001–2010","Chargé de recherche CNRS, Géosciences Rennes."),
            ("2000–2001","Postdoctorant, Institut Weizmann, Israël."),
        ],s),
        section("Formation",s),
        role_table([
            ("2008","Habilitation à diriger des recherches, Université de Rennes 1. Modélisation des écoulements et du transport dans les milieux fortement hétérogènes et fracturés."),
            ("1999","Doctorat, Géosciences Rennes, Université de Rennes 1."),
            ("1995","DEA d’hydrologie et d’hydrogéologie, Université Paris VI."),
            ("1992–1994","École polytechnique."),
        ],s),
        section("Domaines de recherche",s),
        *bullets([
            "Aquifères peu profonds, bassins versants de tête et échanges eaux souterraines–eaux de surface.",
            "Temps de transit, traceurs environnementaux, réactivité et qualité de l’eau.",
            "Modélisation hydrogéologique, hétérogénéité, changement d’échelle et incertitudes.",
            "Changement climatique, ressources en eau et articulation entre hydrosystèmes et empreinte eau.",
        ],s),
        section("Responsabilités scientifiques actuelles",s),
        role_table([
            ("Depuis 2023","PEPR OneWater – Eau Bien Commun : coordination scientifique du PC4 « Empreinte Eau &amp; Eau Sentinelle » avec Hélène Budzinski ; co-animation du Défi 2 « Empreinte eau » avec Hélène Fenet."),
            ("Depuis 2019","Chaire Eaux &amp; Territoires, co-titulaire avec Luc Aquilina, Fondation Université de Rennes."),
            ("Depuis 2025","Conseil scientifique de l’ANDRA ; présidence du conseil de l’OREME."),
            ("Depuis 2024","Membre du GIEC des Pays de la Loire."),
        ],s),
        section("Responsabilités scientifiques antérieures",s),
        role_table([
            ("Jusqu’en 2026","IRIS-E, co-responsable du WP2 « Recherches interdisciplinaires et co-construites » avec Jean-Marc Roussel (INRAE)."),
            ("2018–2024","Président du conseil de l’Observatoire Ecce-Terra, Sorbonne Université."),
            ("2014–2017","Création et animation de RISC-E, groupe interdisciplinaire sur les systèmes complexes en environnement."),
            ("2021–2024","Membre de la commission scientifique spécialisée STEA de l’INRAE."),
        ],s),
        section("Projets de recherche (sélection)",s),
        role_table([
            ("2026–","<b>FutureFlow</b>, ANR PRCI France–Suisse ; coordination avec Clément Roques, modélisation multi-fidélité des bassins de tête."),
            ("2023–","<b>OneWater PC4</b>, France 2030 ; empreinte eau, ACV, fingerprint et eau sentinelle dans les socio-hydrosystèmes."),
            ("2025–","<b>ARCHANGE</b>, risques hydrogéologiques côtiers et changement climatique."),
            ("2024–","<b>NIRECAS</b>, résilience de la qualité de l’eau et nitrates."),
            ("2019–2026","<b>EAUX 2050 / RIVIÈRES 2070 / CYDRE</b>, ressources en eau, scénarios climatiques et prévision saisonnière."),
            ("2019–2025","<b>RIVAGES Normands 2100</b>, remontées de nappes et adaptation des territoires littoraux."),
            ("2014–2019","<b>AquiFR-BZH</b>, évaluation régionale des ressources dans les aquifères de socle."),
        ],s),
        section("Activités éditoriales et responsabilités dans la communauté",s),
        role_table([
            ("2006–2011",link("Hydrogeology Journal","https://link.springer.com/journal/10040")+" : éditeur associé."),
            ("2013–2018",link("Journal of Hydrology","https://www.sciencedirect.com/journal/journal-of-hydrology")+" : éditeur associé."),
            ("2016",link("Journal of Hydrology, numéro spécial","https://doi.org/10.1016/j.jhydrol.2016.11.046")+" : co-éditeur avec Timothy R. Ginn de <i>Residence times in subsurface hydrological systems: signature of hydrological processes and impact on environmental applications</i>."),
            ("2018–2024",link("Computational Methods in Water Resources (CMWR)","https://has.arizona.edu/events/25th-biennial-conference-computational-methods-water-resources")+" : membre du CMWR Committee, chargé de la continuité du cycle international biennal de conférences."),
            ("2018","Co-organisateur de la conférence CMWR à Saint-Malo avec Jocelyne Erhel et Tanguy Le Borgne."),
        ],s),
        section("Encadrement et logiciels",s),
        para("Encadrement et co-encadrement de doctorants, postdoctorants, étudiants de master et stagiaires. Développement de méthodes et de logiciels scientifiques ouverts, notamment "+link("HydroModPy","https://dreuzy.github.io/hydromodpy.html")+" et "+link("PyAges","https://dreuzy.github.io/pyages.html")+".",s),
        section("Publications (sélection)",s),
        Paragraph(f"<b>{PUBLICATION_COUNT} articles publiés</b> référencés dans la bibliographie du site. Liste complète : "+link("bibliographie en ligne","https://dreuzy.github.io/bibliographie.html")+".",s["CVText"]),
        *bullets([
            "Sergeant et al. (2026), <i>Using Landscape Information to Assess Nutrient Recycling in Freshwater Catchments</i>, "+link("Hydrological Processes","https://doi.org/10.1002/hyp.70718")+".",
            "Le Mesnil et al. (2026), <i>Rivages Normands 2100: transdisciplinary co-constructed knowledge for land-use adaptation to groundwater rise along Normandy coastline</i>, "+link("Sustainability Science","https://doi.org/10.1007/s11625-026-01896-8")+".",
            "Gauvain et al. (2026), <i>Technical note: HydroModPy (v1.0)</i>, "+link("Hydrology and Earth System Sciences","https://hess.copernicus.org/articles/30/5571/2026/")+".",
            "Baioni et al. (2026), <i>A regionally based method to identify lithology-specific hydraulic conductivity distributions in shallow aquifers</i>, "+link("Journal of Hydrology","https://doi.org/10.1016/j.jhydrol.2026.135264")+".",
            "Kolbe et al. (2019), <i>Stratification of reactivity determines nitrate removal in groundwater</i>, "+link("PNAS","https://doi.org/10.1073/pnas.1816892116")+".",
        ],s),
        Spacer(1,5),
        Paragraph(f"Actualisé le {UPDATED}",s["CVSmall"]),
    ]
    try:
        doc.build(story)
        changed=not OUT.exists() or OUT.read_bytes()!=tmp.read_bytes()
        if changed and not args.check: os.replace(tmp,OUT)
        else: tmp.unlink()
    finally:
        if tmp.exists(): tmp.unlink()
    if args.check and changed:
        print("CV PDF is stale; run scripts/build_cv_pdf.py.");return 1
    print(OUT);return 0
if __name__=="__main__": raise SystemExit(main())
