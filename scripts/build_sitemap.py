#!/usr/bin/env python3
"""Build the bilingual sitemap from mirror-map.json."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def public_url(base_url: str, path: str) -> str:
    if path == "index.html":
        return f"{base_url}/"
    if path == "en/index.html":
        return f"{base_url}/en/"
    return f"{base_url}/{path}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail instead of rewriting a stale sitemap")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "mirror-map.json").read_text(encoding="utf-8"))
    base_url = manifest["site"].rstrip("/")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    count = 0
    for page in manifest["pages"]:
        if page.get("redirect"):
            continue
        fr_url = public_url(base_url, page["fr"])
        en_url = public_url(base_url, page["en"])
        for location in (fr_url, en_url):
            lines.append(
                "  <url>"
                f"<loc>{html.escape(location)}</loc>"
                f'<xhtml:link rel="alternate" hreflang="fr" href="{html.escape(fr_url, quote=True)}"/>'
                f'<xhtml:link rel="alternate" hreflang="en" href="{html.escape(en_url, quote=True)}"/>'
                f'<xhtml:link rel="alternate" hreflang="x-default" href="{html.escape(fr_url, quote=True)}"/>'
                "</url>"
            )
            count += 1
    lines.append("</urlset>")
    output = "\n".join(lines) + "\n"
    target = ROOT / "sitemap.xml"
    changed = not target.is_file() or target.read_text(encoding="utf-8") != output
    if changed and not args.check:
        target.write_text(output, encoding="utf-8")
    print(f"Sitemap built: {count} URLs.")
    if args.check and changed:
        print("sitemap.xml is stale; run scripts/build_sitemap.py.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
