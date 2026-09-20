#!/usr/bin/env python3
"""Materialize fragmented Base64 figures as direct WebP assets and update pages."""

from __future__ import annotations

import base64
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "figures" / "embedded"


def decode(name: str, count: int) -> Path:
    chunks = []
    for index in range(count):
        path = ROOT / "assets" / "figure-data" / f"{name}.part-{index:02}.txt"
        chunks.append("".join(path.read_text(encoding="utf-8").split()))
    raw = base64.b64decode("".join(chunks), validate=True)
    if not (raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"):
        raise RuntimeError(f"{name}: decoded data is not WebP")
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"{name}.webp"
    target.write_bytes(raw)
    return target


def update_page(path: Path) -> int:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    is_en = path.parent.name == "en"
    changed = 0
    for image in soup.select("img[data-b64-name]"):
        name = image["data-b64-name"]
        count = int(image.get("data-b64-parts", "1"))
        if name == "futureflow-illustration":
            source = ("../" if is_en else "") + "assets/figures/futureflow-framework.webp"
        elif name == "onewater-sentinel":
            source = ("../" if is_en else "") + "assets/figures/onewater.svg"
        else:
            decode(name, count)
            source = ("../" if is_en else "") + f"assets/figures/embedded/{name}.webp"
        image["src"] = source
        for attribute in ("data-b64-name", "data-b64-parts", "data-b64-mime"):
            image.attrs.pop(attribute, None)
        parent = image.parent
        if parent and parent.name == "a" and not parent.get("href"):
            parent.unwrap()
        changed += 1
    for script in list(soup.select('script[src^="figure-loader.js"], script[src="../figure-loader.js"]')):
        script.decompose()
        changed += 1
    if changed:
        path.write_text(str(soup), encoding="utf-8")
    return changed


def main() -> None:
    pages = sorted(ROOT.glob("*.html")) + sorted((ROOT / "en").glob("*.html"))
    changes = sum(update_page(page) for page in pages)
    print(f"Materialized embedded figures; applied {changes} page updates.")


if __name__ == "__main__":
    main()
