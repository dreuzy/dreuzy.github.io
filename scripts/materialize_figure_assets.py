#!/usr/bin/env python3
"""Rebuild and verify direct WebP assets from their Base64 source fragments."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from argparse import ArgumentParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "assets" / "figure-data"
MANIFEST = DATA / "manifest.json"


def decode(name: str, count: int) -> bytes:
    chunks = []
    for index in range(count):
        path = DATA / f"{name}.part-{index:02}.txt"
        if not path.is_file():
            raise RuntimeError(f"{name}: missing source fragment {path.relative_to(ROOT)}")
        chunks.append("".join(path.read_text(encoding="utf-8").split()))
    raw = base64.b64decode("".join(chunks), validate=True)
    if not (raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"):
        raise RuntimeError(f"{name}: decoded data is not WebP")
    return raw


def verify(raw: bytes, item: dict[str, object]) -> None:
    name = str(item["name"])
    expected_size = int(item["bytes"])
    expected_hash = str(item["sha256"])
    actual_hash = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_size:
        raise RuntimeError(f"{name}: {len(raw)} bytes, expected {expected_size}")
    if actual_hash != expected_hash:
        raise RuntimeError(f"{name}: SHA-256 {actual_hash}, expected {expected_hash}")


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify outputs without rewriting them")
    parser.add_argument("--name", action="append", default=[], help="limit processing to a figure name")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    wanted = set(args.name)
    selected = [item for item in manifest["figures"] if not wanted or item["name"] in wanted]
    missing_names = wanted - {item["name"] for item in selected}
    if missing_names:
        print(f"Unknown figure(s): {', '.join(sorted(missing_names))}", file=sys.stderr)
        return 2

    changed = 0
    for item in selected:
        raw = decode(str(item["name"]), int(item["parts"]))
        verify(raw, item)
        target = ROOT / str(item["output"])
        if target.is_file() and target.read_bytes() == raw:
            continue
        if args.check:
            print(f"Outdated or missing figure: {target.relative_to(ROOT)}", file=sys.stderr)
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        changed += 1

    verb = "verified" if args.check else "materialized"
    print(f"Figure assets {verb}: {len(selected)} checked, {changed} rewritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
