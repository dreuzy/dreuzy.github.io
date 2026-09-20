#!/usr/bin/env python3
"""Synchronize shared navigation, footer, language links and canonical metadata."""

from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "site-config.json"
MIRROR_PATH = ROOT / "mirror-map.json"


def relative_link(source: str, target: str) -> str:
    parent = str(PurePosixPath(source).parent)
    return posixpath.relpath(target, "." if parent == "." else parent)


def public_url(base_url: str, path: str) -> str:
    if path == "index.html":
        return f"{base_url}/"
    if path == "en/index.html":
        return f"{base_url}/en/"
    return f"{base_url}/{path}"


def shared_blocks(
    config: dict[str, object],
    manifest: dict[str, object],
    page: dict[str, object],
    lang: str,
) -> tuple[str, str, str]:
    page_id = page["id"]
    source = page[lang]
    other_lang = "en" if lang == "fr" else "fr"
    by_id = {item["id"]: item for item in manifest["pages"]}
    section = config["page_sections"].get(page_id)
    navigation = []
    for item in config["navigation"]:
        target = by_id[item["id"]][lang]
        attributes = ""
        if section == item["id"]:
            current = "page" if page_id == item["id"] else "location"
            attributes = f' aria-current="{current}" class="active"'
        navigation.append(
            f'<a{attributes} href="{html.escape(relative_link(source, target), quote=True)}">'
            f'{html.escape(item[lang])}</a>'
        )

    switch_target = relative_link(source, page[other_lang])
    if lang == "fr":
        language_switch = f'<span><strong>FR</strong> | <a href="{html.escape(switch_target, quote=True)}">EN</a></span>'
        nav_label = "Navigation principale"
        skip = "Aller au contenu"
        contact_label = "Courriel"
    else:
        language_switch = f'<span><a href="{html.escape(switch_target, quote=True)}">FR</a> | <strong>EN</strong></span>'
        nav_label = "Main navigation"
        skip = "Skip to content"
        contact_label = "Email"

    home = relative_link(source, by_id["home"][lang])
    header = (
        '<header class="site-header"><div class="inner">'
        f'<a class="brand-link" href="{html.escape(home, quote=True)}">{html.escape(config["name"])}</a>'
        f'<nav aria-label="{nav_label}" class="nav-links">'
        f'{"".join(navigation)}{language_switch}</nav></div></header>'
    )
    organizations = " · ".join(config["footer_organizations"])
    contact = config["contact"]
    footer = (
        '<footer class="preview-footer"><div class="inner">'
        f'<span>{html.escape(config["name"])} · {html.escape(organizations)}</span>'
        '<span class="footer-contact">'
        f'<a href="mailto:{html.escape(contact["email"], quote=True)}">{contact_label}</a> · '
        f'<a href="{html.escape(contact["orcid"], quote=True)}" rel="me noopener" target="_blank">ORCID</a> · '
        f'<a href="{html.escape(contact["hal"], quote=True)}" rel="noopener" target="_blank">HAL</a>'
        '</span></div></footer>'
    )
    return f'<a class="skip-link" href="#main-content">{skip}</a>', header, footer


def replace_one(source: str, pattern: str, replacement: str, label: str, path: str) -> str:
    output, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=re.DOTALL | re.IGNORECASE)
    if count != 1:
        raise RuntimeError(f"{path}: expected one {label}, found {count}")
    return output


def update_person_jsonld(source: str, config: dict[str, object]) -> str:
    pattern = r'(<script\b(?=[^>]*\btype="application/ld\+json")[^>]*>)(.*?)(</script>)'

    def replacement(match: re.Match[str]) -> str:
        try:
            payload = json.loads(match.group(2))
        except json.JSONDecodeError:
            return match.group(0)
        if payload.get("@type") != "Person":
            return match.group(0)
        contact = config["contact"]
        payload["image"] = contact["portrait"]
        payload["sameAs"] = [
            contact["orcid"],
            contact["hal"],
            contact["scholar"],
            contact["github"],
            contact["directory"],
        ]
        compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return f"{match.group(1)}{compact}{match.group(3)}"

    return re.sub(pattern, replacement, source, flags=re.DOTALL | re.IGNORECASE)


def update_metadata(source: str, config: dict[str, object], page: dict[str, object], lang: str) -> str:
    path = page[lang]
    base_url = config["base_url"]
    canonical = public_url(base_url, path)
    fr_url = public_url(base_url, page["fr"])
    en_url = public_url(base_url, page["en"])
    section = config["page_sections"].get(page["id"], "research")
    social = config["social_images"].get(section, config["social_images"]["research"])
    social_url = f'{base_url}/{social["path"]}'
    replacements = [
        (r'<link\b(?=[^>]*\brel="canonical")[^>]*>', f'<link href="{canonical}" rel="canonical"/>', "canonical"),
        (r'<link\b(?=[^>]*\bhreflang="fr")[^>]*>', f'<link href="{fr_url}" hreflang="fr" rel="alternate"/>', "hreflang fr"),
        (r'<link\b(?=[^>]*\bhreflang="en")[^>]*>', f'<link href="{en_url}" hreflang="en" rel="alternate"/>', "hreflang en"),
        (r'<link\b(?=[^>]*\bhreflang="x-default")[^>]*>', f'<link href="{fr_url}" hreflang="x-default" rel="alternate"/>', "hreflang x-default"),
        (r'<meta\b(?=[^>]*\bproperty="og:url")[^>]*>', f'<meta content="{canonical}" property="og:url"/>', "og:url"),
        (r'<meta\b(?=[^>]*\bproperty="og:image")[^>]*>', f'<meta content="{social_url}" property="og:image"/>', "og:image"),
        (r'<meta\b(?=[^>]*\bproperty="og:image:width")[^>]*>', '<meta content="1200" property="og:image:width"/>', "og:image:width"),
        (r'<meta\b(?=[^>]*\bproperty="og:image:height")[^>]*>', '<meta content="630" property="og:image:height"/>', "og:image:height"),
        (r'<meta\b(?=[^>]*\bproperty="og:image:alt")[^>]*>', f'<meta content="{html.escape(social[lang], quote=True)}" property="og:image:alt"/>', "og:image:alt"),
        (r'<meta\b(?=[^>]*\bname="twitter:image")[^>]*>', f'<meta content="{social_url}" name="twitter:image"/>', "twitter:image"),
        (r'<meta\b(?=[^>]*\bname="twitter:image:alt")[^>]*>', f'<meta content="{html.escape(social[lang], quote=True)}" name="twitter:image:alt"/>', "twitter:image:alt"),
    ]
    for pattern, replacement, label in replacements:
        source = replace_one(source, pattern, replacement, label, path)
    return update_person_jsonld(source, config)


def render_page(
    source: str,
    config: dict[str, object],
    manifest: dict[str, object],
    page: dict[str, object],
    lang: str,
) -> str:
    path = page[lang]
    skip, header, footer = shared_blocks(config, manifest, page, lang)
    source = replace_one(source, r'<a\s+class="skip-link".*?</a>', skip, "skip link", path)
    source = replace_one(source, r'<header\s+class="site-header".*?</header>', header, "site header", path)
    source = replace_one(source, r'<footer\s+class="preview-footer".*?</footer>', footer, "site footer", path)
    source = source.replace("assets/figures/onewater.svg", "assets/figures/onewater-sentinel.webp")
    source = re.sub(
        r'<img\b[^>]*\bfutureflow-framework\.webp[^>]*>',
        lambda match: re.sub(
            r'\b(height|width)="\d+"',
            lambda dimension: 'height="540"' if dimension.group(1) == "height" else 'width="720"',
            match.group(0),
        ),
        source,
        flags=re.IGNORECASE,
    )
    return update_metadata(source, config, page, lang)


def render_404(source: str, config: dict[str, object], manifest: dict[str, object]) -> str:
    by_id = {item["id"]: item for item in manifest["pages"]}
    navigation = []
    for item in config["navigation"]:
        target = by_id[item["id"]]["fr"]
        navigation.append(
            f'<a href="{html.escape(relative_link("404.html", target), quote=True)}">{html.escape(item["fr"])}</a>'
        )
    home = relative_link("404.html", by_id["home"]["fr"])
    header = (
        '<header class="site-header"><div class="inner">'
        f'<a class="brand-link" href="{home}">{html.escape(config["name"])}</a>'
        '<nav aria-label="Navigation principale" class="nav-links">'
        f'{"".join(navigation)}</nav></div></header>'
    )
    organizations = " · ".join(config["footer_organizations"])
    contact = config["contact"]
    footer = (
        '<footer class="preview-footer"><div class="inner">'
        f'<span>{html.escape(config["name"])} · {html.escape(organizations)}</span>'
        '<span class="footer-contact">'
        f'<a href="mailto:{html.escape(contact["email"], quote=True)}">Courriel</a> · '
        f'<a href="{html.escape(contact["orcid"], quote=True)}" rel="me noopener" target="_blank">ORCID</a> · '
        f'<a href="{html.escape(contact["hal"], quote=True)}" rel="noopener" target="_blank">HAL</a>'
        '</span></div></footer>'
    )
    source = replace_one(source, r'<a\s+class="skip-link".*?</a>', '<a class="skip-link" href="#main-content">Aller au contenu</a>', "skip link", "404.html")
    source = replace_one(source, r'<header\s+class="site-header".*?</header>', header, "site header", "404.html")
    return replace_one(source, r'<footer\s+class="preview-footer".*?</footer>', footer, "site footer", "404.html")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated shared blocks are stale")
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MIRROR_PATH.read_text(encoding="utf-8"))
    stale: list[str] = []

    for page in manifest["pages"]:
        if page.get("redirect"):
            continue
        for lang in ("fr", "en"):
            path = ROOT / page[lang]
            source = path.read_text(encoding="utf-8")
            output = render_page(source, config, manifest, page, lang)
            if output == source:
                continue
            stale.append(page[lang])
            if not args.check:
                path.write_text(output, encoding="utf-8")

    path_404 = ROOT / "404.html"
    source_404 = path_404.read_text(encoding="utf-8")
    output_404 = render_404(source_404, config, manifest)
    if output_404 != source_404:
        stale.append("404.html")
        if not args.check:
            path_404.write_text(output_404, encoding="utf-8")

    if args.check and stale:
        print("Shared layout is stale:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    print(f"Shared layout {'checked' if args.check else 'synchronized'}: {len(stale)} file(s) changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
