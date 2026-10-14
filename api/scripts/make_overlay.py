"""
make_overlay.py
===============
Generates the three PNGs (before, after, overlay) for an event and saves
them to /cache/<event_id>/.

Usage:
    python api/scripts/make_overlay.py himachal_2023
    python api/scripts/make_overlay.py assam_2022
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "api"))


def make(event_id: str) -> None:
    from config import DATA_DIR, CACHE_DIR
    from schemas import Event

    meta   = Event.model_validate_json((DATA_DIR / event_id / "meta.json").read_text())
    cache_dir = CACHE_DIR / event_id
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Clear cached PNGs so they are regenerated
    for f in ["before_thumb.png", "after_thumb.png", "overlay_thumb.png"]:
        (cache_dir / f).unlink(missing_ok=True)

    from agent.tools.vision import _prepare_images
    imgs = _prepare_images(meta)
    if imgs:
        before_png, after_png, overlay_png = imgs
        print(f"  before  : {before_png}")
        print(f"  after   : {after_png}")
        print(f"  overlay : {overlay_png}")
    else:
        print("  ERROR: Could not generate images (rasterio unavailable?)")


if __name__ == "__main__":
    event_ids = sys.argv[1:] or ["himachal_2023", "assam_2022"]
    for eid in event_ids:
        print(f"\n=== {eid} ===")
        make(eid)