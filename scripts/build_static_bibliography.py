#!/usr/bin/env python3
"""Render the bilingual static bibliography from editable structured JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bibliography.json"
PAGES = {"fr": ROOT / "bibliographie.html", "en": ROOT / "en" / "bibliography.html"}


def load_data() -> dict[str, object]:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise RuntimeError("Unsupported bibliography schema version")
    return data


def render_content(data: dict[str, object], lang: str) -> BeautifulSoup:
    fragment = BeautifulSoup("", "html.parser")
    seen_ids: set[str] = set()

    for section in data["sections"]:
        heading = fragment.new_tag("h2", id=section["id"])
        heading.string = section["title"][lang]
        fragment.append(heading)

        for group in section["groups"]:
            if group["title"] is not None:
                subheading = fragment.new_tag("h3", id=group["id"])
                subheading.string = group["title"][lang]
                fragment.append(subheading)

            list_tag = fragment.new_tag("ol" if group["ordered"] else "ul")
            if group["classes"]:
                list_tag["class"] = group["classes"]
            for entry in group["entries"]:
                entry_id = entry["id"]
                if entry_id in seen_ids:
                    raise RuntimeError(f"Duplicate bibliography entry id: {entry_id}")
                seen_ids.add(entry_id)
                item = fragment.new_tag("li", attrs={"data-bib-id": entry_id})
                entry_fragment = BeautifulSoup(entry["html"][lang], "html.parser")
                item.extend(list(entry_fragment.contents))
                list_tag.append(item)
            fragment.append(list_tag)

    return fragment


def update_page(path: Path, content: BeautifulSoup, check: bool = False) -> bool:
    source = path.read_text(encoding="utf-8")
    page = BeautifulSoup(source, "html.parser")
    host = page.select_one("#bibliography-content")
    if host is None:
        raise RuntimeError(f"Missing #bibliography-content in {path.relative_to(ROOT)}")
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
        changed += update_page(path, render_content(data, lang), args.check)

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
