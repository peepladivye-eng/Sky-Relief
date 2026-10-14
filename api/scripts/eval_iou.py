"""
eval_iou.py
===========
Evaluates the flood mask against a reference mask (ref_mask.tif).
Prints IoU (Intersection over Union) and F1 score.

Usage:
    python api/scripts/eval_iou.py himachal_2023
    python api/scripts/eval_iou.py assam_2022
    python api/scripts/eval_iou.py  # runs both
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "api"))


def evaluate(event_id: str) -> dict:
    import numpy as np
    from config import DATA_DIR
    from schemas import Event
    import json

    event_dir = DATA_DIR / event_id
    ref_path  = event_dir / "ref_mask.tif"

    meta = Event.model_validate_json((event_dir / "meta.json").read_text())

    print(f"\n=== {event_id} ===")
    print(f"Event: {meta.name}")

    # Compute predicted mask
    from agent.tools.raster import get_flood_mask_array
    pred_mask, transform = get_flood_mask_array(meta)
    pred = pred_mask.astype(bool)

    # Load reference mask
    if not ref_path.exists():
        print("  No ref_mask.tif found — skipping IoU eval")
        area_km2 = float(pred.sum()) * abs(transform.a) * abs(transform.e) * (111.32**2)
        print(f"  Predicted flood area: {area_km2:.2f} km2")
        print(f"  Predicted flood pixels: {pred.sum():,} / {pred.size:,} ({100*pred.mean():.1f}%)")
        return {"event_id": event_id, "iou": None, "f1": None, "area_km2": area_km2}

    import rasterio
    with rasterio.open(ref_path) as src:
        ref_data = src.read(1)
        nodata   = src.nodata

    ref = (ref_data == 1)
    if nodata is not None:
        valid = ref_data != nodata
        ref   = (ref_data == 1) & valid
        # Crop pred to valid area
        pred  = pred & valid

    # Resize if shapes differ (nearest-neighbour)
    if pred.shape != ref.shape:
        from skimage.transform import resize
        pred = resize(pred.astype(float), ref.shape, order=0, anti_aliasing=False) > 0.5

    intersection = (pred & ref).sum()
    union        = (pred | ref).sum()
    iou          = intersection / union if union > 0 else 0.0

    tp = intersection
    fp = (pred & ~ref).sum()
    fn = (~pred & ref).sum()
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    area_km2 = float(pred.sum()) * abs(transform.a) * abs(transform.e) * (111.32**2)

    print(f"  Predicted flood pixels : {pred.sum():,} ({100*pred.mean():.1f}%)")
    print(f"  Reference flood pixels : {ref.sum():,}  ({100*ref.mean():.1f}%)")
    print(f"  Intersection           : {intersection:,}")
    print(f"  Union                  : {union:,}")
    print(f"  IoU                    : {iou:.4f}  {'(target > 0.5)' if iou >= 0.5 else '(BELOW target 0.5 -- see README)'}")
    print(f"  Precision              : {precision:.4f}")
    print(f"  Recall                 : {recall:.4f}")
    print(f"  F1                     : {f1:.4f}")
    print(f"  Area (predicted)       : {area_km2:.2f} km2")

    return {"event_id": event_id, "iou": round(iou, 4),
            "f1": round(f1, 4), "area_km2": round(area_km2, 2)}


if __name__ == "__main__":
    event_ids = sys.argv[1:] or ["himachal_2023", "assam_2022"]
    results = [evaluate(eid) for eid in event_ids]

    print("\n=== SUMMARY TABLE ===")
    print(f"{'Event':<20} {'IoU':>6} {'F1':>6} {'Area km2':>10}")
    print("-" * 46)
    for r in results:
        iou = f"{r['iou']:.4f}" if r["iou"] is not None else "  N/A"
        f1  = f"{r['f1']:.4f}"  if r["f1"]  is not None else "  N/A"
        print(f"{r['event_id']:<20} {iou:>6} {f1:>6} {r['area_km2']:>10.2f}")

    print("\nNote: ref_mask.tif is synthetically generated to match the flood")
    print("extent baked into the fixture rasters. IoU > 0.5 expected by design.")
    print("For real-world validation, replace ref_mask.tif with a Copernicus EMS")
    print("or Sen1Floods11 hand-labelled mask.")