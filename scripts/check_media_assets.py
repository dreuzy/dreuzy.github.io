#!/usr/bin/env python3
"""Decode every published raster image and parse every SVG asset."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RASTER_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


def check_raster(path: Path) -> None:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        image.load()
        if image.width < 1 or image.height < 1:
            raise ValueError("invalid dimensions")


def main() -> int:
    failures: list[str] = []
    checked = 0
    for path in sorted((ROOT / "assets").rglob("*")):
        if not path.is_file():
            continue
        try:
            if path.suffix.lower() in RASTER_EXTENSIONS:
                check_raster(path)
            elif path.suffix.lower() == ".svg":
                ET.parse(path)
            else:
                continue
            checked += 1
        except Exception as exc:  # noqa: BLE001 - report every decoder/parser failure together
            failures.append(f"{path.relative_to(ROOT)}: {exc}")

    if failures:
        print("Invalid media assets:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Media assets checked: {checked} raster/SVG files decoded successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
