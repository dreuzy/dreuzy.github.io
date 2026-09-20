#!/usr/bin/env python3
"""Run persistent SEO, accessibility, sitemap and bibliography integrity checks."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]


def public_url(base_url: str, path: str) -> str:
    if path == "index.html":
        return f"{base_url}/"
    if path == "en/index.html":
        return f"{base_url}/en/"
    return f"{base_url}/{path}"


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def rel_values(tag) -> set[str]:
    value = tag.get("rel", [])
    return {item.lower() for item in (value if isinstance(value, list) else value.split())}


def find_group(data: dict[str, object], section_id: str, group_id: str) -> dict[str, object]:
    for section in data["sections"]:
        if section["id"] == section_id:
            for group in section["groups"]:
                if group["id"] == group_id:
                    return group
    raise RuntimeError(f"Missing bibliography group {section_id}/{group_id}")


def article_record(entry: dict[str, object]) -> tuple[str, str, set[str], set[str]]:
    soup = BeautifulSoup(entry["html"]["fr"], "html.parser")
    title_links = [
        link.get_text(" ", strip=True)
        for link in soup.select("a")
        if len(link.get_text(" ", strip=True)) > 15
        and not link.get_text(" ", strip=True).startswith("[")
    ]
    if not title_links:
        raise RuntimeError(f"No linked title for {entry['id']}")
    title = title_links[0]
    text = soup.get_text(" ", strip=True)
    authors_text = re.split(r"\((?:19|20)\d{2}\)", text, maxsplit=1)[0]
    authors = set(normalized(authors_text).split())
    dois: set[str] = set()
    for link in soup.select('a[href*="doi.org/"]'):
        match = re.search(r"doi\.org/(10\.[^?#\s]+)", link.get("href", ""), flags=re.I)
        if match:
            dois.add(match.group(1).rstrip(".,;)").lower())
    return title, normalized(title), authors, dois


def check_bibliography(config: dict[str, object], errors: list[str]) -> None:
    data = json.loads((ROOT / "data" / "bibliography.json").read_text(encoding="utf-8"))
    expected = config["bibliography_reference_counts"]
    published = find_group(
        data,
        "articles-dans-des-revues-a-comite-de-lecture",
        "articles-publies",
    )["entries"]
    abstracts = find_group(data, "abstracts-de-colloques", "entries")["entries"]
    proceedings = find_group(
        data,
        "proceedings-references-dans-web-of-knowledge",
        "entries",
    )["entries"]
    actual_counts = {
        "published_articles": len(published),
        "conference_abstracts": len(abstracts),
        "proceedings": len(proceedings),
    }
    if actual_counts != expected:
        errors.append(f"bibliography reference counts differ: {actual_counts}, expected {expected}")

    all_entries = [
        entry
        for section in data["sections"]
        for group in section["groups"]
        for entry in group["entries"]
    ]
    ids = [entry["id"] for entry in all_entries]
    duplicate_ids = sorted({value for value in ids if ids.count(value) > 1})
    if duplicate_ids:
        errors.append(f"duplicate bibliography entry ids: {duplicate_ids}")
    for entry in all_entries:
        for lang in ("fr", "en"):
            if not entry.get("html", {}).get(lang, "").strip():
                errors.append(f"{entry['id']}: empty {lang.upper()} bibliography content")

    records = []
    title_index: dict[str, list[str]] = defaultdict(list)
    doi_index: dict[str, list[str]] = defaultdict(list)
    for entry in published:
        try:
            title, title_norm, authors, dois = article_record(entry)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        records.append((entry["id"], title, title_norm, authors))
        title_index[title_norm].append(entry["id"])
        for doi in dois:
            doi_index[doi].append(entry["id"])
    for title, entry_ids in title_index.items():
        if len(entry_ids) > 1:
            errors.append(f"duplicate published-article title {title!r}: {entry_ids}")
    for doi, entry_ids in doi_index.items():
        if len(entry_ids) > 1:
            errors.append(f"duplicate published-article DOI {doi}: {entry_ids}")

    allow_data = json.loads(
        (ROOT / "data" / "bibliography-duplicate-allowlist.json").read_text(encoding="utf-8")
    )
    allowed = {tuple(sorted(item["ids"])) for item in allow_data["pairs"]}
    candidates: set[tuple[str, str]] = set()
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            title_similarity = SequenceMatcher(None, left[2], right[2]).ratio()
            author_similarity = len(left[3] & right[3]) / max(1, len(left[3] | right[3]))
            if title_similarity >= 0.80 or (title_similarity >= 0.72 and author_similarity >= 0.95):
                pair = tuple(sorted((left[0], right[0])))
                candidates.add(pair)
                if pair not in allowed:
                    errors.append(
                        "unreviewed near-duplicate articles "
                        f"{pair[0]} / {pair[1]} "
                        f"(title={title_similarity:.3f}, authors={author_similarity:.3f}): "
                        f"{left[1]!r} / {right[1]!r}"
                    )
    stale_allowed = sorted(allowed - candidates)
    if stale_allowed:
        errors.append(f"stale bibliography duplicate allowlist pairs: {stale_allowed}")

    expected_ids = set(ids)
    for path in (ROOT / "bibliographie.html", ROOT / "en" / "bibliography.html"):
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        rendered_ids = {item.get("data-bib-id") for item in soup.select("#bibliography-content li[data-bib-id]")}
        if rendered_ids != expected_ids:
            errors.append(
                f"{path.relative_to(ROOT)}: rendered bibliography ids differ "
                f"(rendered={len(rendered_ids)}, source={len(expected_ids)})"
            )


def check_page(
    path: Path,
    relative: str,
    expected_lang: str,
    expected_canonical: str,
    fr_url: str,
    en_url: str,
    errors: list[str],
) -> str | None:
    source = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(source, "html.parser")
    prefix = f"{relative}:"
    if not soup.html or soup.html.get("lang") != expected_lang:
        errors.append(f"{prefix} html lang must be {expected_lang}")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if not title:
        errors.append(f"{prefix} missing title")
    description = soup.select_one('meta[name="description"]')
    if not description or len(description.get("content", "").strip()) < 50:
        errors.append(f"{prefix} missing or too-short meta description")
    canonical_tag = soup.select_one('link[rel~="canonical"]')
    canonical = canonical_tag.get("href") if canonical_tag else None
    if canonical != expected_canonical:
        errors.append(f"{prefix} canonical is {canonical!r}, expected {expected_canonical!r}")
    alternates = {
        tag.get("hreflang"): tag.get("href")
        for tag in soup.select('link[rel~="alternate"][hreflang]')
    }
    expected_alternates = {"fr": fr_url, "en": en_url, "x-default": fr_url}
    if alternates != expected_alternates:
        errors.append(f"{prefix} hreflang links are {alternates}, expected {expected_alternates}")
    robots = soup.select_one('meta[name="robots"]')
    if robots and "noindex" in robots.get("content", "").lower():
        errors.append(f"{prefix} content page must not be noindex")
    if len(soup.find_all("h1")) != 1:
        errors.append(f"{prefix} must contain exactly one h1")
    if not soup.select_one("main#main-content"):
        errors.append(f"{prefix} missing main#main-content")
    if not soup.select_one('a.skip-link[href="#main-content"]'):
        errors.append(f"{prefix} missing skip link")
    if not soup.select_one("header.site-header nav.nav-links"):
        errors.append(f"{prefix} missing shared navigation")
    if not soup.select_one("footer.preview-footer"):
        errors.append(f"{prefix} missing shared footer")
    required_social = [
        ('meta[property="og:title"]', "og:title"),
        ('meta[property="og:description"]', "og:description"),
        ('meta[property="og:url"]', "og:url"),
        ('meta[property="og:image"]', "og:image"),
        ('meta[name="twitter:card"]', "twitter:card"),
        ('meta[name="twitter:title"]', "twitter:title"),
        ('meta[name="twitter:description"]', "twitter:description"),
        ('meta[name="twitter:image"]', "twitter:image"),
    ]
    for selector, label in required_social:
        tag = soup.select_one(selector)
        if not tag or not tag.get("content", "").strip():
            errors.append(f"{prefix} missing {label}")
    og_url = soup.select_one('meta[property="og:url"]')
    if og_url and og_url.get("content") != expected_canonical:
        errors.append(f"{prefix} og:url does not match canonical")
    ids = [tag.get("id") for tag in soup.select("[id]")]
    duplicate_ids = sorted({value for value in ids if ids.count(value) > 1})
    if duplicate_ids:
        errors.append(f"{prefix} duplicate HTML ids: {duplicate_ids}")
    for image in soup.find_all("img"):
        if not image.get("alt", "").strip():
            errors.append(f"{prefix} image {image.get('src')!r} has no useful alt text")
        for dimension in ("width", "height"):
            if not str(image.get(dimension, "")).isdigit():
                errors.append(f"{prefix} image {image.get('src')!r} has no intrinsic {dimension}")
    for link in soup.select('a[target="_blank"]'):
        if "noopener" not in rel_values(link):
            errors.append(f"{prefix} target=_blank link lacks rel=noopener: {link.get('href')}")
    if "data-b64-" in source or "figure-loader.js" in source:
        errors.append(f"{prefix} legacy in-browser figure loader is still present")
    return title or None


def main() -> int:
    config = json.loads((ROOT / "site-config.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "mirror-map.json").read_text(encoding="utf-8"))
    base_url = config["base_url"].rstrip("/")
    errors: list[str] = []
    canonical_urls: list[str] = []
    page_titles: dict[tuple[str, str], list[str]] = defaultdict(list)
    mapped_files: set[str] = set()
    expected_sitemap: list[str] = []

    nav_ids = [item["id"] for item in config["navigation"]]
    if nav_ids != manifest["navigation"]:
        errors.append(f"site-config navigation ids {nav_ids} differ from mirror-map {manifest['navigation']}")

    for page in manifest["pages"]:
        mapped_files.update((page["fr"], page["en"]))
        if page.get("redirect"):
            for lang in ("fr", "en"):
                path = ROOT / page[lang]
                soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
                robots = soup.select_one('meta[name="robots"]')
                if not robots or "noindex" not in robots.get("content", "").lower():
                    errors.append(f"{page[lang]}: redirect must be noindex")
            continue
        if page["id"] not in config["page_sections"]:
            errors.append(f"{page['id']}: missing page_sections mapping")
        fr_url = public_url(base_url, page["fr"])
        en_url = public_url(base_url, page["en"])
        for lang, url in (("fr", fr_url), ("en", en_url)):
            relative = page[lang]
            expected_sitemap.append(url)
            title = check_page(ROOT / relative, relative, lang, url, fr_url, en_url, errors)
            canonical_urls.append(url)
            if title:
                page_titles[(lang, title)].append(relative)

    duplicates = sorted(url for url in set(canonical_urls) if canonical_urls.count(url) > 1)
    if duplicates:
        errors.append(f"duplicate canonical URLs: {duplicates}")
    duplicate_titles = {f"{lang}:{title}": paths for (lang, title), paths in page_titles.items() if len(paths) > 1}
    if duplicate_titles:
        errors.append(f"duplicate page titles: {duplicate_titles}")

    all_html = {
        str(path.relative_to(ROOT))
        for path in [*ROOT.glob("*.html"), *(ROOT / "en").glob("*.html")]
    }
    expected_html = mapped_files | {"404.html"}
    if all_html != expected_html:
        errors.append(
            f"unmapped/missing HTML files: extra={sorted(all_html - expected_html)}, "
            f"missing={sorted(expected_html - all_html)}"
        )
    error_page = BeautifulSoup((ROOT / "404.html").read_text(encoding="utf-8"), "html.parser")
    robots_404 = error_page.select_one('meta[name="robots"]')
    if not robots_404 or "noindex" not in robots_404.get("content", "").lower():
        errors.append("404.html: error page must be noindex")

    tree = ET.parse(ROOT / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = [node.text or "" for node in tree.findall("sm:url/sm:loc", namespace)]
    if sitemap_urls != expected_sitemap:
        errors.append(
            f"sitemap URLs differ (found {len(sitemap_urls)}, expected {len(expected_sitemap)}); "
            "run scripts/build_sitemap.py"
        )

    legacy_payloads = sorted(path.name for path in ROOT.glob("bibliographie-payload-*.txt"))
    if legacy_payloads:
        errors.append(f"legacy opaque bibliography payloads remain: {legacy_payloads}")
    if (ROOT / "scripts" / "apply_site_audit.py").exists():
        errors.append("one-time migration script scripts/apply_site_audit.py should be archived or removed")

    check_bibliography(config, errors)

    if errors:
        print("Site quality check FAILED:\n", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"Site quality check passed: {len(expected_sitemap)} indexable pages, "
        f"{len(all_html)} HTML files, bibliography and sitemap verified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
