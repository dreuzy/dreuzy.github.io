#!/usr/bin/env python3
"""Render the bilingual static bibliography from editable structured JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bibliography.json"
PAGES = {"fr": ROOT / "bibliographie.html", "en": ROOT / "en" / "bibliography.html"}
PUBLICATION_PAGES = {"fr": ROOT / "publications.html", "en": ROOT / "en" / "publications.html"}
STATUS_GROUPS = {
    "en-preparation": {"fr": "En préparation", "en": "In preparation", "class": "preparation"},
    "articles-soumis": {"fr": "Soumis", "en": "Submitted", "class": "submitted"},
    "in-review": {"fr": "En révision", "en": "In revision", "class": "review"},
    "accepted": {"fr": "Accepté", "en": "Accepted", "class": "accepted"},
}


def load_data() -> dict[str, object]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise RuntimeError("Unsupported bibliography schema version")
    return data


def render_content(data: dict[str, object], lang: str) -> BeautifulSoup:
    fragment = BeautifulSoup("", "html.parser")
    seen_ids: set[str] = set()

    for section in data["sections"]:
        heading = fragment.new_tag("h2", id=section["id"], attrs={"data-bib-heading": "section"})
        heading.string = section["title"][lang]
        fragment.append(heading)

        for group in section["groups"]:
            if group["title"] is not None:
                subheading = fragment.new_tag("h3", id=group["id"], attrs={"data-bib-heading": "group"})
                subheading.string = group["title"][lang]
                fragment.append(subheading)

            list_tag = fragment.new_tag("ol" if group["ordered"] else "ul")
            list_tag["data-bib-section"] = section["id"]
            list_tag["data-bib-group"] = group["id"]
            if group["classes"]:
                list_tag["class"] = group["classes"]
            for entry in group["entries"]:
                entry_id = entry["id"]
                if entry_id in seen_ids:
                    raise RuntimeError(f"Duplicate bibliography entry id: {entry_id}")
                seen_ids.add(entry_id)
                entry_fragment = BeautifulSoup(entry["html"][lang], "html.parser")
                plain_text = entry_fragment.get_text(" ", strip=True)
                year_match = re.search(r"\b(?:19|20)\d{2}\b", plain_text)
                item = fragment.new_tag(
                    "li",
                    attrs={
                        "data-bib-id": entry_id,
                        "data-bib-section": section["id"],
                        "data-bib-group": group["id"],
                        "data-bib-year": year_match.group(0) if year_match else "",
                    },
                )
                if group["id"] in STATUS_GROUPS:
                    status = STATUS_GROUPS[group["id"]]
                    badge = fragment.new_tag("span", attrs={"class": ["status-badge", f'status-{status["class"]}']})
                    badge.string = status[lang]
                    item.append(badge)
                item.extend(list(entry_fragment.contents))
                list_tag.append(item)
            fragment.append(list_tag)

    return fragment


def filter_markup(lang: str) -> BeautifulSoup:
    if lang == "fr":
        markup = """
<form class="bibliography-tools" id="bibliography-filters" role="search">
  <label for="bib-search">Mots-clés<input id="bib-search" name="q" placeholder="Titre, auteur, revue…" type="search"/></label>
  <label for="bib-type">Type<select id="bib-type" name="type"><option value="">Tous les types</option><option value="articles-dans-des-revues-a-comite-de-lecture">Articles</option><option value="rapports-et-autres-publications">Rapports</option><option value="chapitre-douvrage">Chapitres</option><option value="proceedings-references-dans-web-of-knowledge">Actes</option><option value="abstracts-de-colloques">Abstracts</option></select></label>
  <label for="bib-year">Année<select id="bib-year" name="year"><option value="">Toutes les années</option></select></label>
  <button type="reset">Effacer</button>
</form>
<p class="bibliography-count" id="bibliography-count" aria-live="polite"></p>
"""
    else:
        markup = """
<form class="bibliography-tools" id="bibliography-filters" role="search">
  <label for="bib-search">Keywords<input id="bib-search" name="q" placeholder="Title, author, journal…" type="search"/></label>
  <label for="bib-type">Type<select id="bib-type" name="type"><option value="">All types</option><option value="articles-dans-des-revues-a-comite-de-lecture">Articles</option><option value="rapports-et-autres-publications">Reports</option><option value="chapitre-douvrage">Chapters</option><option value="proceedings-references-dans-web-of-knowledge">Proceedings</option><option value="abstracts-de-colloques">Abstracts</option></select></label>
  <label for="bib-year">Year<select id="bib-year" name="year"><option value="">All years</option></select></label>
  <button type="reset">Clear</button>
</form>
<p class="bibliography-count" id="bibliography-count" aria-live="polite"></p>
"""
    return BeautifulSoup(markup, "html.parser")


def render_recent(data: dict[str, object], lang: str, limit: int = 6) -> BeautifulSoup:
    fragment = BeautifulSoup("", "html.parser")
    articles = next(section for section in data["sections"] if section["id"] == "articles-dans-des-revues-a-comite-de-lecture")
    published = next(group for group in articles["groups"] if group["id"] == "articles-publies")
    for entry in published["entries"][:limit]:
        container = fragment.new_tag("div", attrs={"class": "pub-entry", "data-bib-id": entry["id"]})
        citation = BeautifulSoup(entry["html"][lang], "html.parser")
        title_link = citation.find("a", href=True)
        if title_link:
            prefix = citation.get_text(" ", strip=True).split(title_link.get_text(" ", strip=True), 1)[0]
            year = re.search(r"\b(?:19|20)\d{2}\b", prefix)
            first_author = prefix.split(",", 1)[0].strip()
            journal = citation.select_one(".smallcaps")
            title = fragment.new_tag("div", attrs={"class": "pub-title"})
            anchor = fragment.new_tag("a", attrs=dict(title_link.attrs))
            anchor.string = title_link.get_text(" ", strip=True)
            title.append(anchor)
            meta = fragment.new_tag("div", attrs={"class": "pub-meta"})
            author_label = first_author + (" et al." if lang == "fr" else " et al.")
            parts = [author_label + (f" ({year.group(0)})" if year else "")]
            if journal:
                parts.append(journal.get_text(" ", strip=True))
            meta.string = " · ".join(parts)
            container.extend([title, meta])
        else:
            container.extend(list(citation.contents))
        fragment.append(container)
    link = fragment.new_tag("p", attrs={"class": "backlink"})
    anchor = fragment.new_tag("a", href="bibliographie.html" if lang == "fr" else "bibliography.html")
    anchor.string = "Voir la bibliographie complète →" if lang == "fr" else "View the full bibliography →"
    link.append(anchor)
    fragment.append(link)
    return fragment


def update_page(path: Path, content: BeautifulSoup, lang: str, check: bool = False) -> bool:
    source = path.read_text(encoding="utf-8")
    page = BeautifulSoup(source, "html.parser")
    host = page.select_one("#bibliography-content")
    if host is None:
        raise RuntimeError(f"Missing #bibliography-content in {path.relative_to(ROOT)}")
    host.clear()
    host.extend(list(content.contents))
    old_filters = page.select_one("#bibliography-filters")
    if old_filters:
        old_count = page.select_one("#bibliography-count")
        old_filters.decompose()
        if old_count:
            old_count.decompose()
    filters = filter_markup(lang)
    toc = page.select_one(".bib-toc")
    toc.insert_before(filters.form)
    toc.insert_before(filters.select_one("#bibliography-count"))
    if not page.find("script", src=("bibliography-filter.js" if lang == "fr" else "../bibliography-filter.js")):
        script = page.new_tag("script", src="bibliography-filter.js" if lang == "fr" else "../bibliography-filter.js")
        page.body.append(script)
    output = str(page)
    if output == source:
        return False
    if not check:
        path.write_text(output, encoding="utf-8")
    return True


def update_recent_page(path: Path, content: BeautifulSoup, check: bool = False) -> bool:
    source = path.read_text(encoding="utf-8")
    page = BeautifulSoup(source, "html.parser")
    host = page.select_one("#recent-publications-list")
    if host is None:
        raise RuntimeError(f"Missing #recent-publications-list in {path.relative_to(ROOT)}")
    host.clear()
    host.extend(list(content.contents))
    output = str(page)
    if output == source:
        return False
    if not check:
        path.write_text(output, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail instead of rewriting stale pages")
    args = parser.parse_args()
    data = load_data()
    changed = 0
    for lang, path in PAGES.items():
        changed += update_page(path, render_content(data, lang), lang, args.check)
        changed += update_recent_page(PUBLICATION_PAGES[lang], render_recent(data, lang), args.check)

    group_counts = {
        (section["id"], group["id"]): len(group["entries"])
        for section in data["sections"]
        for group in section["groups"]
    }
    published = group_counts[("articles-dans-des-revues-a-comite-de-lecture", "articles-publies")]
    abstracts = group_counts[("abstracts-de-colloques", "entries")]
    proceedings = group_counts[("proceedings-references-dans-web-of-knowledge", "entries")]
    print(
        "Static bibliography built: "
        f"{published} published articles, {abstracts} abstracts, "
        f"{proceedings} proceedings, {changed} page(s) rewritten."
    )
    if args.check and changed:
        print("Run scripts/build_static_bibliography.py to refresh the pages.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
