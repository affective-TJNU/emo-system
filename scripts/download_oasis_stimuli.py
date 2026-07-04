#!/usr/bin/env python3
"""Download 9 emotion images from OASIS (open research stimulus set) into seed_emotion/."""

from __future__ import annotations

import csv
import io
import json
import urllib.request
import zipfile
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("请先安装 Pillow: pip install pillow") from exc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "MetaBCI-master" / "stimuli" / "seed_emotion"
CACHE = ROOT / "MetaBCI-master" / "stimuli" / "_oasis_cache"

OASIS_ZIP_URL = "https://osf.io/download/uxvpb/"

# Theme names from OASIS.csv (valence-normed); picked for demo suitability
SELECTION = {
    "positive": ["Dog 6", "Beach 1", "Penguins 2"],
    "neutral": ["Desert 1", "Cardboard 2", "Paperclips 1"],
    "negative": ["Garbage dump 3", "Spider 1", "Tornado 1"],
}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    print(f"downloading {dest.name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "emo-system/1.0 (research demo)"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as fh:
        fh.write(resp.read())


def _load_oasis_rows(zf: zipfile.ZipFile) -> list[dict]:
    raw = zf.read("OASIS.csv").decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(raw)))


def _theme_to_zip_path(theme: str) -> str:
    return f"images/{theme}.jpg"


def _save_png(src_bytes: bytes, dest: Path, *, max_size=(800, 600)) -> None:
    img = Image.open(io.BytesIO(src_bytes)).convert("RGB")
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", max_size, (16, 16, 24))
    ox = (max_size[0] - img.width) // 2
    oy = (max_size[1] - img.height) // 2
    canvas.paste(img, (ox, oy))
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest, format="PNG", optimize=True)


def main() -> int:
    zip_path = CACHE / "OASIS.zip"
    _download(OASIS_ZIP_URL, zip_path)

    manifest: dict = {
        "source": "OASIS (Open Affective Standardized Image Set)",
        "citation": "Kurdi, Lozano, & Banaji (2017), Behavior Research Methods",
        "license": "Research use; see https://osf.io/6pnd7/",
        "images": [],
    }

    with zipfile.ZipFile(zip_path) as zf:
        rows = {r["Theme"]: r for r in _load_oasis_rows(zf)}
        for emotion, themes in SELECTION.items():
            folder = OUT / emotion
            for idx, theme in enumerate(themes, start=1):
                zip_name = _theme_to_zip_path(theme)
                if zip_name not in zf.namelist():
                    raise FileNotFoundError(f"OASIS image missing in zip: {theme}")
                meta = rows.get(theme, {})
                out_name = f"{emotion}_{idx:02d}.png"
                out_path = folder / out_name
                _save_png(zf.read(zip_name), out_path)
                entry = {
                    "emotion": emotion,
                    "filename": out_name,
                    "oasis_theme": theme,
                    "oasis_valence_mean": float(meta.get("Valence_mean") or 0),
                    "oasis_category": meta.get("Category", ""),
                }
                manifest["images"].append(entry)
                print(f"wrote {out_path} <- OASIS '{theme}' (valence={entry['oasis_valence_mean']:.2f})")

    manifest_path = OUT / "STIMULI_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone. {len(manifest['images'])} images -> {OUT}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
