#!/usr/bin/env python3
"""Check local links and local static resources in the website HTML files."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []
        self.anchors: set[str] = set()

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self._attrs(attrs)
        if values.get("id"):
            self.anchors.add(values["id"])
        if tag == "a" and values.get("name"):
            self.anchors.add(values["name"])
        if tag in {"a", "link"} and values.get("href"):
            self.refs.append((f"{tag} href", values["href"]))
        elif tag in {"script", "img", "source"} and values.get("src"):
            self.refs.append((f"{tag} src", values["src"]))
        elif tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            content = values.get("content", "")
            lower = content.lower()
            marker = "url="
            if marker in lower:
                idx = lower.index(marker) + len(marker)
                self.refs.append(("meta refresh", content[idx:].strip(" \"'")))


def local_target(source: Path, ref: str) -> Path | None:
    ref = ref.strip()
    if not ref:
        return source
    parts = urlsplit(ref)
    if parts.scheme or parts.netloc:
        return None
    path = parts.path
    if not path:
        return source
    if path.startswith("/"):
        target = ROOT / path.lstrip("/")
    else:
        target = source.parent / path
    target = target.resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return target
    if target.is_dir():
        target = target / "index.html"
    return target


def main() -> int:
    pages = sorted(ROOT.glob("*.html")) + sorted((ROOT / "en").glob("*.html"))
    errors: list[str] = []
    checked = 0
    anchor_cache: dict[Path, set[str]] = {}

    def anchors(path: Path) -> set[str]:
        if path not in anchor_cache:
            parser = LinkParser()
            parser.feed(path.read_text(encoding="utf-8"))
            parser.close()
            anchor_cache[path] = parser.anchors
        return anchor_cache[path]

    for page in pages:
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parser.close()
        for kind, ref in parser.refs:
            target = local_target(page, ref)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                errors.append(
                    f"{page.relative_to(ROOT)}: {kind}={ref!r} -> "
                    f"missing {target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}"
                )
                continue
            fragment = unquote(urlsplit(ref).fragment)
            if fragment and target.suffix.lower() in {".html", ".htm"} and fragment not in anchors(target):
                errors.append(
                    f"{page.relative_to(ROOT)}: {kind}={ref!r} -> "
                    f"missing anchor #{fragment} in {target.relative_to(ROOT)}"
                )

    if errors:
        print("Local link check FAILED:\n", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Local link check passed: {len(pages)} HTML pages, {checked} local references checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
