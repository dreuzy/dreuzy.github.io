#!/usr/bin/env python3
"""Validate the one-to-one French/English structure of the static website.

The check deliberately ignores prose so that the two languages can be edited
independently. It verifies page pairing, navigation, reciprocal language links,
layout blocks and figure identity. This prevents structural drift without
altering any figure or page content.
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "mirror-map.json"

STRUCTURAL_CLASSES = (
    "home-hero",
    "home-sections",
    "research-row",
    "project-row",
    "section-block",
    "people-entry",
    "people-grid",
    "pub-entry",
    "secondary-project",
    "software-mark",
    "timeline-row",
    "figure-panel",
)


@dataclass
class ParsedPage:
    lang: str | None = None
    h1_count: int = 0
    nav_depth: int = 0
    nav_links: list[tuple[str, str]] = field(default_factory=list)
    _link_href: str | None = None
    _link_text: list[str] = field(default_factory=list)
    class_counts: Counter[str] = field(default_factory=Counter)
    figures: list[tuple[str, ...]] = field(default_factory=list)
    inline_svg_count: int = 0
    meta_refresh: str | None = None


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page = ParsedPage()

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self._attrs(attrs)

        if tag == "html":
            self.page.lang = values.get("lang") or None
        elif tag == "h1":
            self.page.h1_count += 1
        elif tag == "nav" and "nav-links" in values.get("class", "").split():
            self.page.nav_depth += 1
        elif tag == "a" and self.page.nav_depth:
            self.page._link_href = values.get("href", "")
            self.page._link_text = []
        elif tag == "img":
            generated_name = values.get("data-b64-name")
            if generated_name:
                self.page.figures.append(
                    (
                        "generated",
                        generated_name,
                        values.get("data-b64-parts", ""),
                    )
                )
            else:
                src = values.get("src", "")
                if src:
                    self.page.figures.append(("image", posixpath.basename(urlsplit(src).path)))
        elif tag == "svg":
            self.page.inline_svg_count += 1
        elif tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            match = re.search(r"url\s*=\s*([^;]+)$", values.get("content", ""), re.I)
            if match:
                self.page.meta_refresh = match.group(1).strip(" \"'")

        for class_name in values.get("class", "").split():
            if class_name in STRUCTURAL_CLASSES:
                self.page.class_counts[class_name] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.page.nav_depth and self.page._link_href is not None:
            text = " ".join("".join(self.page._link_text).split())
            self.page.nav_links.append((text, self.page._link_href))
            self.page._link_href = None
            self.page._link_text = []
        elif tag == "nav" and self.page.nav_depth:
            self.page.nav_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.page._link_href is not None:
            self.page._link_text.append(data)


def parse_page(path: Path) -> ParsedPage:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.page


def normalize_target(source: str, href: str) -> str | None:
    """Resolve a local href to a repository-relative path."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or href.startswith("mailto:"):
        return None
    target = parts.path
    if not target:
        target = posixpath.basename(source)
    source_dir = posixpath.dirname(source)
    resolved = posixpath.normpath(posixpath.join(source_dir, target))
    if resolved == ".":
        resolved = "index.html"
    if resolved.endswith("/"):
        resolved += "index.html"
    return resolved.lstrip("/")


def navigation_ids(
    page: ParsedPage,
    source_path: str,
    language: str,
    path_to_id: dict[str, dict[str, str]],
) -> list[str]:
    ids: list[str] = []
    for text, href in page.nav_links:
        if text.strip().upper() in {"FR", "EN"}:
            continue
        target = normalize_target(source_path, href)
        if target and target in path_to_id[language]:
            ids.append(path_to_id[language][target])
    return ids


def opposite_language_target(page: ParsedPage, source_path: str, language: str) -> str | None:
    wanted = "EN" if language == "fr" else "FR"
    for text, href in page.nav_links:
        if text.strip().upper() == wanted:
            return normalize_target(source_path, href)
    return None


def format_counts(counter: Counter[str]) -> str:
    return ", ".join(f"{key}={counter.get(key, 0)}" for key in STRUCTURAL_CLASSES)


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    pages = manifest["pages"]
    expected_navigation = manifest["navigation"]

    path_to_id: dict[str, dict[str, str]] = {"fr": {}, "en": {}}
    id_to_path: dict[str, dict[str, str]] = {"fr": {}, "en": {}}
    for item in pages:
        for language in ("fr", "en"):
            path = item[language]
            path_to_id[language][path] = item["id"]
            id_to_path[language][item["id"]] = path

    errors: list[str] = []
    checked = 0

    for item in pages:
        page_id = item["id"]
        fr_rel = item["fr"]
        en_rel = item["en"]
        fr_path = ROOT / fr_rel
        en_path = ROOT / en_rel

        for language, rel, path in (("fr", fr_rel, fr_path), ("en", en_rel, en_path)):
            if not path.is_file():
                errors.append(f"[{page_id}] missing {language.upper()} page: {rel}")
        if not fr_path.is_file() or not en_path.is_file():
            continue

        fr = parse_page(fr_path)
        en = parse_page(en_path)
        checked += 1

        if fr.lang != "fr":
            errors.append(f"[{page_id}] {fr_rel} must declare <html lang=\"fr\">")
        if en.lang != "en":
            errors.append(f"[{page_id}] {en_rel} must declare <html lang=\"en\">")

        if item.get("redirect"):
            target_id = item["target"]
            expected_fr = id_to_path["fr"][target_id]
            expected_en = id_to_path["en"][target_id]
            actual_fr = normalize_target(fr_rel, fr.meta_refresh or "")
            actual_en = normalize_target(en_rel, en.meta_refresh or "")
            if actual_fr != expected_fr:
                errors.append(f"[{page_id}] FR redirect points to {actual_fr!r}, expected {expected_fr!r}")
            if actual_en != expected_en:
                errors.append(f"[{page_id}] EN redirect points to {actual_en!r}, expected {expected_en!r}")
            continue

        if fr.h1_count != 1 or en.h1_count != 1:
            errors.append(
                f"[{page_id}] each page must contain one H1 "
                f"(FR={fr.h1_count}, EN={en.h1_count})"
            )

        if item.get("navigation"):
            fr_nav = navigation_ids(fr, fr_rel, "fr", path_to_id)
            en_nav = navigation_ids(en, en_rel, "en", path_to_id)
            if fr_nav != expected_navigation:
                errors.append(f"[{page_id}] FR navigation order is {fr_nav}, expected {expected_navigation}")
            if en_nav != expected_navigation:
                errors.append(f"[{page_id}] EN navigation order is {en_nav}, expected {expected_navigation}")

        fr_switch = opposite_language_target(fr, fr_rel, "fr")
        en_switch = opposite_language_target(en, en_rel, "en")
        if fr_switch != en_rel:
            errors.append(f"[{page_id}] FR→EN switch points to {fr_switch!r}, expected {en_rel!r}")
        if en_switch != fr_rel:
            errors.append(f"[{page_id}] EN→FR switch points to {en_switch!r}, expected {fr_rel!r}")

        if fr.class_counts != en.class_counts:
            errors.append(
                f"[{page_id}] structural blocks differ\n"
                f"  FR: {format_counts(fr.class_counts)}\n"
                f"  EN: {format_counts(en.class_counts)}"
            )

        if fr.figures != en.figures:
            errors.append(
                f"[{page_id}] figure references differ\n"
                f"  FR: {fr.figures}\n"
                f"  EN: {en.figures}"
            )
        if fr.inline_svg_count != en.inline_svg_count:
            errors.append(
                f"[{page_id}] inline SVG counts differ "
                f"(FR={fr.inline_svg_count}, EN={en.inline_svg_count})"
            )

    if errors:
        print("Bilingual mirror check FAILED:\n", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Bilingual mirror check passed: {checked} page pairs, "
        f"{len(expected_navigation)} mirrored navigation entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
