#!/usr/bin/env python3
"""Rebuild deterministic FR/EN publication-history figures from structured data."""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["svg.hashsalt"] = "dreuzy-publication-history"
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "bibliography.json"
DATA_OUT = ROOT / "publications-au-fil-du-temps-data.json"
FR_SVG = ROOT / "publications-au-fil-du-temps.svg"
EN_SVG = ROOT / "en" / "publications-au-fil-du-temps.svg"
FR_PAGE = ROOT / "publications-au-fil-du-temps.html"
EN_PAGE = ROOT / "en" / "publications-over-time.html"


def load_bibliography() -> dict[str, object]:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def collect_group(data: dict[str, object], section_id: str, group_id: str) -> list[str]:
    for section in data["sections"]:
        if section["id"] != section_id:
            continue
        for group in section["groups"]:
            if group["id"] == group_id:
                return [
                    BeautifulSoup(entry["html"]["fr"], "html.parser").get_text(" ", strip=True)
                    for entry in group["entries"]
                ]
    raise RuntimeError(f"Bibliography group not found: {section_id}/{group_id}")


def year_counts(entries: list[str]) -> Counter[int]:
    counts: Counter[int] = Counter()
    for entry in entries:
        match = re.search(r"\((19\d{2}|20\d{2})\)", entry) or re.search(r"\b(19\d{2}|20\d{2})\b", entry)
        if match:
            counts[int(match.group(1))] += 1
    return counts


def moving_average(values: np.ndarray, window: int = 5) -> np.ndarray:
    out = np.full_like(values, np.nan, dtype=float)
    valid = np.where(~np.isnan(values))[0]
    half = window // 2
    for i in valid:
        lo = max(valid[0], i - half)
        hi = min(valid[-1], i + half)
        out[i] = np.nanmean(values[lo:hi + 1])
    return out


def nice_even_ceiling(value: float, minimum: int) -> int:
    return max(minimum, int(math.ceil(value / 2.0) * 2))


def update_history_page(
    path: Path,
    lang: str,
    article_counts: Counter[int],
    abstract_counts: Counter[int],
    proceedings_counts: Counter[int],
    max_year: int,
    check: bool = False,
) -> bool:
    article_peak_year, article_peak = max(article_counts.items(), key=lambda item: (item[1], -item[0]))
    abstract_peak_year, abstract_peak = max(abstract_counts.items(), key=lambda item: (item[1], -item[0]))
    if lang == "fr":
        summary = (
            f"Le corpus comprend {sum(article_counts.values())} articles, "
            f"{sum(abstract_counts.values())} abstracts de colloques et "
            f"{sum(proceedings_counts.values())} proceedings. "
            f"Le maximum annuel d’articles a été atteint en {article_peak_year} "
            f"({article_peak} articles) ; celui des abstracts en {abstract_peak_year} ({abstract_peak})."
        )
    else:
        summary = (
            f"The record covers {sum(article_counts.values())} journal articles, "
            f"{sum(abstract_counts.values())} conference abstracts and "
            f"{sum(proceedings_counts.values())} proceedings. "
            f"The strongest annual article output was in {article_peak_year} "
            f"({article_peak} papers); conference abstracts peaked in {abstract_peak_year} ({abstract_peak})."
        )
    rows = "".join(
        f'<tr><th scope="row">{year}</th><td>{article_counts.get(year, 0)}</td>'
        f'<td>{abstract_counts.get(year, 0)}</td><td>{proceedings_counts.get(year, 0)}</td></tr>'
        for year in range(2000, max_year + 1)
    )
    source = path.read_text(encoding="utf-8")
    output, summary_count = re.subn(
        r'(<p class="lead publication-summary">).*?(</p>)',
        lambda match: f"{match.group(1)}{summary}{match.group(2)}",
        source,
        count=1,
        flags=re.DOTALL,
    )
    output, table_count = re.subn(
        r"(<tbody>).*?(</tbody>)",
        lambda match: f"{match.group(1)}{rows}{match.group(2)}",
        output,
        count=1,
        flags=re.DOTALL,
    )
    if summary_count != 1 or table_count != 1:
        raise RuntimeError(f"{path.relative_to(ROOT)}: missing publication summary or annual table")
    changed = output != source
    if changed and not check:
        path.write_text(output, encoding="utf-8")
    return changed


def build_svg(path: Path, years: np.ndarray, articles: np.ndarray, abstracts: np.ndarray,
              ma_articles: np.ndarray, ma_abstracts: np.ndarray, lang: str,
              check: bool = False) -> bool:
    fr = lang == "fr"
    labels = {
        "year": "Année" if fr else "Year",
        "articles_axis": "Articles publiés par année" if fr else "Published articles per year",
        "abstracts_axis": "Abstracts de colloques par année" if fr else "Conference abstracts per year",
        "articles": "Articles publiés" if fr else "Published articles",
        "articles_ma": "Articles (moyenne mobile 5 ans)" if fr else "Articles (5-year moving average)",
        "abstracts": "Abstracts de colloques" if fr else "Conference abstracts",
        "abstracts_ma": "Abstracts (moyenne mobile 5 ans)" if fr else "Abstracts (5-year moving average)",
        "thesis": "Thèse" if fr else "PhD",
        "israel": "Israël" if fr else "Israel",
        "barcelona": "Barcelone / CSIC–UPC" if fr else "Barcelona / CSIC–UPC",
        "osur": "Direction OSUR" if fr else "OSUR Director",
        "vp": "VP Rech." if fr else "VP Research",
        "pres": "Présidence" if fr else "President",
        "ens": "ENS Rennes",
        "made": f"Réalisation {int(years[-1])}" if fr else f"Produced in {int(years[-1])}",
    }

    color_pub = "#2B6CB0"
    color_ma_pub = "#123B63"
    color_abs = "#8FA39A"
    color_ma_abs = "#5F7A6E"
    color_band = "#F6F7F8"
    color_career = "#666666"
    color_text = "#30343B"

    max_year = int(years[-1])
    article_max = nice_even_ceiling(float(np.nanmax(articles)), 12)
    abstract_max = article_max * 2

    fig = plt.figure(figsize=(18, 10.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[4.9, 1.35], hspace=0.18)
    ax = fig.add_subplot(gs[0])
    ax_r = ax.twinx()

    l1, = ax.plot(years, articles, color=color_pub, linestyle="--", linewidth=2.0,
                  marker="o", markersize=4.2, alpha=0.9, label=labels["articles"], zorder=4)
    l2, = ax.plot(years, ma_articles, color=color_ma_pub, linewidth=3.3,
                  label=labels["articles_ma"], zorder=5)
    l3, = ax_r.plot(years, abstracts, color=color_abs, linestyle=":", linewidth=1.8,
                    marker="o", markersize=3.2, alpha=0.65, label=labels["abstracts"], zorder=2)
    l4, = ax_r.plot(years, ma_abstracts, color=color_ma_abs, linewidth=1.5,
                    label=labels["abstracts_ma"], zorder=3)

    ax.set_xlim(1998, max_year + 0.8)
    ax.set_ylim(0, article_max)
    ax_r.set_ylim(0, abstract_max)
    ax.set_xlabel(labels["year"], fontsize=18, labelpad=8)
    ax.set_ylabel(labels["articles_axis"], fontsize=18, color=color_pub, labelpad=12)
    ax_r.set_ylabel(labels["abstracts_axis"], fontsize=18, color=color_abs, labelpad=14)
    ticks = list(range(1998, max_year + 1, 2))
    if max_year not in ticks:
        ticks.append(max_year)
    ax.set_xticks(ticks)
    ax.tick_params(axis="x", labelsize=14)
    ax.tick_params(axis="y", labelsize=14, labelcolor=color_pub)
    ax_r.tick_params(axis="y", labelsize=14, labelcolor=color_abs)
    ax.grid(axis="y", alpha=0.16)
    ax.spines["top"].set_visible(False)
    ax_r.spines["top"].set_visible(False)

    fig.legend([l1, l2, l3, l4], [x.get_label() for x in (l1, l2, l3, l4)],
               loc="upper center", bbox_to_anchor=(0.5, 0.992), ncol=4, fontsize=13.5, frameon=False)
    fig.text(0.985, 0.018, labels["made"], ha="right", va="bottom", fontsize=14, color=color_text)

    band = fig.add_subplot(gs[1], sharex=ax)
    band.set_facecolor(color_band)
    band.set_ylim(0, 1)
    band.set_yticks([])
    band.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
    for side in ("left", "right", "top", "bottom"):
        band.spines[side].set_visible(False)

    band.plot(1999, 0.80, marker="o", markersize=6, color=color_career)
    band.text(1999, 0.88, f"{labels['thesis']}\n1999", ha="center", va="bottom", fontsize=13, color=color_text)
    band.plot(2008, 0.80, marker="o", markersize=6, color=color_career)
    band.text(2008, 0.88, "HDR\n2008", ha="center", va="bottom", fontsize=13, color=color_text)

    for start, end, label in (
        (2000.0, 2001.0, f"{labels['israel']}\n2000–2001"),
        (2011.0, 2013.0, f"{labels['barcelona']}\n2011–2013"),
    ):
        band.hlines(0.50, start, end, color=color_career, linewidth=3.8)
        band.vlines([start, end], 0.455, 0.545, color=color_career, linewidth=1.2)
        band.text((start + end) / 2, 0.58, label, ha="center", va="bottom", fontsize=13, color=color_text)

    presidency_end = max(max_year + 0.8, 2026.8)
    for start, end, label, fs in (
        (2017.0, 2021.0, f"{labels['osur']}\n2017–2021", 12.5),
        (2021.0, 2026.0, f"{labels['vp']}\n{labels['ens']}\n2021–2026", 12),
        (2026.0, presidency_end, f"{labels['pres']}\n{labels['ens']}\n2026–", 12),
    ):
        band.hlines(0.20, start, end, color=color_career, linewidth=3.8)
        band.vlines([start, end], 0.155, 0.245, color=color_career, linewidth=1.2)
        band.text((start + end) / 2, 0.28, label, ha="center", va="bottom", fontsize=fs,
                  color=color_text, linespacing=0.95)

    fig.subplots_adjust(left=0.075, right=0.91, top=0.91, bottom=0.12)
    output = io.BytesIO()
    fig.savefig(
        output,
        format="svg",
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "dreuzy.github.io"},
    )
    plt.close(fig)
    # Matplotlib leaves spaces at a few SVG path line endings. Normalize them so
    # `git diff --check` and repeated builds stay clean across environments.
    svg = output.getvalue().decode("utf-8")
    raw = ("\n".join(line.rstrip() for line in svg.splitlines()) + "\n").encode("utf-8")
    changed = not path.is_file() or path.read_bytes() != raw
    if changed and not check:
        path.write_bytes(raw)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail instead of rewriting stale outputs")
    args = parser.parse_args()
    data_source = load_bibliography()
    articles = collect_group(
        data_source,
        "articles-dans-des-revues-a-comite-de-lecture",
        "articles-publies",
    )
    abstracts = collect_group(data_source, "abstracts-de-colloques", "entries")
    proceedings = collect_group(
        data_source,
        "proceedings-references-dans-web-of-knowledge",
        "entries",
    )

    article_counts = year_counts(articles)
    abstract_counts = year_counts(abstracts)
    proceedings_counts = year_counts(proceedings)
    combined_counts = abstract_counts + proceedings_counts

    all_years = set(article_counts) | set(combined_counts) | {date.today().year}
    max_year = max(all_years)
    years = np.arange(1998, max_year + 1)
    article_values = np.array([article_counts.get(int(y), np.nan if y < 2000 else 0) for y in years], dtype=float)
    abstract_values = np.array([combined_counts.get(int(y), np.nan if y < 2000 else 0) for y in years], dtype=float)

    ma_articles = moving_average(article_values)
    ma_abstracts = moving_average(abstract_values)

    data = {
        "source": "data/bibliography.json",
        "through_year": max_year,
        "articles": dict(sorted(article_counts.items())),
        "abstracts": dict(sorted(abstract_counts.items())),
        "proceedings": dict(sorted(proceedings_counts.items())),
        "abstracts_including_proceedings": dict(sorted(combined_counts.items())),
    }
    output = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    data_changed = not DATA_OUT.is_file() or DATA_OUT.read_text(encoding="utf-8") != output
    if data_changed and not args.check:
        DATA_OUT.write_text(output, encoding="utf-8")
    fr_changed = build_svg(
        FR_SVG, years, article_values, abstract_values, ma_articles, ma_abstracts, "fr", args.check
    )
    en_changed = build_svg(
        EN_SVG, years, article_values, abstract_values, ma_articles, ma_abstracts, "en", args.check
    )
    fr_page_changed = update_history_page(
        FR_PAGE, "fr", article_counts, abstract_counts, proceedings_counts, max_year, args.check
    )
    en_page_changed = update_history_page(
        EN_PAGE, "en", article_counts, abstract_counts, proceedings_counts, max_year, args.check
    )

    print(f"Articles: {sum(article_counts.values())}")
    print(f"Abstracts: {sum(abstract_counts.values())}")
    print(f"Proceedings added to abstracts: {sum(proceedings_counts.values())}")
    print(f"Years through: {max_year}")
    if args.check and (data_changed or fr_changed or en_changed or fr_page_changed or en_page_changed):
        print("Publication-history outputs are stale; run scripts/build_publications_over_time.py.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
