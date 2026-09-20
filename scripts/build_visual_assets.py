#!/usr/bin/env python3
"""Build deterministic diagrams and social cards used across the website."""

from __future__ import annotations

import argparse
import base64
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "assets" / "figures"
SOCIAL = ROOT / "assets" / "social"
PORTRAIT = ROOT / "assets" / "portrait-jean-raynald-de-dreuzy.jpg"
PORTRAIT_SOURCE = ROOT / "assets" / "figure-data" / "portrait-jrd.part-00.txt"
FONT_REGULAR = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
FONT_BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FONT_SERIF = Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")

NAVY = "#17324a"
INK = "#2f3e49"
BLUE = "#3c789d"
PALE = "#eef4f7"
SOFT = "#f7f9fb"
LINE = "#d9e2e8"


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def webp_bytes(image: Image.Image, *, quality: int = 92) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "WEBP", quality=quality, method=6)
    return buffer.getvalue()


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def portrait_bytes() -> bytes:
    encoded = "".join(PORTRAIT_SOURCE.read_text(encoding="ascii").split())
    return base64.b64decode(encoded, validate=True)


def rounded_box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    *,
    fill: str,
) -> None:
    draw.rounded_rectangle(xy, radius=22, fill=fill, outline="#9eb4c2", width=3)
    left, top, right, bottom = xy
    draw.text((left + 28, top + 28), title, font=font(FONT_BOLD, 28), fill=NAVY)
    draw.multiline_text(
        (left + 28, top + 78),
        subtitle,
        font=font(FONT_REGULAR, 21),
        fill=INK,
        spacing=7,
    )


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line((start, end), fill=BLUE, width=6)
    x, y = end
    draw.polygon(((x, y), (x - 18, y - 11), (x - 18, y + 11)), fill=BLUE)


def build_futureflow() -> bytes:
    image = Image.new("RGB", (1200, 750), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 58), "FutureFlow", font=font(FONT_SERIF, 54), fill=NAVY)
    draw.text(
        (72, 128),
        "Multi-fidelity groundwater modelling for headwater catchments",
        font=font(FONT_REGULAR, 27),
        fill="#526570",
    )

    boxes = [
        ((65, 235, 365, 455), "Low fidelity", "Fast regional\nscreening", PALE),
        ((450, 235, 750, 455), "Medium fidelity", "Catchment\nensembles", SOFT),
        ((835, 235, 1135, 455), "High fidelity", "Process insight\nand benchmarks", PALE),
    ]
    for xy, title, subtitle, fill in boxes:
        rounded_box(draw, xy, title, subtitle, fill=fill)
    arrow(draw, (375, 345), (438, 345))
    arrow(draw, (760, 345), (823, 345))

    draw.rounded_rectangle((150, 550, 1050, 665), radius=20, fill=NAVY)
    draw.text(
        (213, 579),
        "Observations  ↔  calibration  ↔  uncertainty  ↔  regional assessment",
        font=font(FONT_REGULAR, 24),
        fill="white",
    )
    return webp_bytes(image)


def build_hydromodpy_approved() -> bytes:
    source = FIGURES / "embedded" / "hydromodpy-final.webp"
    with Image.open(source) as image:
        return webp_bytes(image.convert("RGB"))


def build_social_card(label: str, accent: str) -> bytes:
    image = Image.new("RGB", (1200, 630), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 24, 630), fill=accent)
    draw.ellipse((890, -140, 1310, 280), fill=PALE)
    draw.ellipse((970, 390, 1260, 680), fill=SOFT, outline=LINE, width=3)
    draw.line((78, 134, 720, 134), fill=LINE, width=3)
    draw.text((78, 178), "Jean-Raynald", font=font(FONT_SERIF, 65), fill=NAVY)
    draw.text((78, 256), "de Dreuzy", font=font(FONT_SERIF, 65), fill=NAVY)
    draw.multiline_text(
        (82, 382),
        label,
        font=font(FONT_REGULAR, 31),
        fill="#526570",
        spacing=9,
    )
    draw.text(
        (82, 540),
        "Hydrogeology · Water resources · Modelling",
        font=font(FONT_REGULAR, 22),
        fill=BLUE,
    )
    return png_bytes(image)


def expected_assets() -> dict[Path, bytes]:
    cards = {
        "profile.png": ("President of ENS Rennes\nCNRS Research Director", "#17324a"),
        "research.png": ("Research · Recherche", "#3c789d"),
        "projects.png": ("Projects & grants · Projets & contrats", "#547f6f"),
        "team.png": ("Supervision & collaborations", "#765d82"),
        "publications.png": ("Publications", "#845d50"),
        "software.png": ("Open-source scientific software", "#386f75"),
        "science-society.png": ("Science & society · Science & société", "#846f43"),
    }
    outputs = {
        FIGURES / "futureflow-framework.webp": build_futureflow(),
        FIGURES / "hydromodpy-approved.webp": build_hydromodpy_approved(),
        PORTRAIT: portrait_bytes(),
    }
    outputs.update({SOCIAL / name: build_social_card(label, accent) for name, (label, accent) in cards.items()})
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when generated visuals are stale")
    args = parser.parse_args()
    stale: list[str] = []
    outputs = expected_assets()
    for path, expected in outputs.items():
        current = path.read_bytes() if path.exists() else None
        if current == expected:
            continue
        stale.append(str(path.relative_to(ROOT)))
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)

    if args.check and stale:
        print("Generated visual assets are stale:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    action = "checked" if args.check else "built"
    print(f"Visual assets {action}: {len(outputs)} files, {len(stale)} stale.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
