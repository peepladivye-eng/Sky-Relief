"""
vision.py - Tool 2
==================
Sends before/after/overlay PNGs to the VLM and returns a VisionCheck.

HARD RULE: The VLM does NOT compute the flood mask. It only verifies,
flags false positives, describes damage, and notes caveats.

Prompt contract (spec section 10):
  "Check whether the red mask matches visible flooding.
   Report only visible evidence.
   List likely false positives (shadow, terrain, cloud).
   Do not estimate casualties."
"""
from __future__ import annotations
import logging
from pathlib import Path
import numpy as np
log = logging.getLogger(__name__)
from config import CACHE_DIR, DATA_DIR
from schemas import Event, FloodStats, VisionCheck, LLMError
from llm import vlm_json, llm_available

_SYSTEM = (
    "You are a satellite imagery analyst assisting a disaster-response team. "
    "You will receive three images: before-flood, after-flood, and an overlay "
    "with the computed flood mask shown in red. "
    "RULES: 1. Report ONLY what is visible. 2. Do NOT estimate casualties. "
    "3. Do NOT override or recompute the flood mask. "
    "4. List suspected false positives (shadow, terrain, cloud). "
    "5. Note visible damage to infrastructure or buildings. "
    "6. State caveats (cloud cover, low contrast, SAR speckle). "
    "Return ONLY valid JSON, no markdown fences."
)

_USER = (
    "Three images attached: [1] before-event, [2] after-event, "
    "[3] flood-mask overlay (red = computed flood extent). "
    "Verify the mask and describe visible conditions. "
    'Return JSON: {"mask_plausible": bool, "false_positive_notes": [str], '
    '"damage_observations": [str], "caveats": [str], "confidence": float}'
)

_OFFLINE_VISION = VisionCheck(
    mask_plausible=True,
    false_positive_notes=[
        "VLM unavailable - mask not visually verified.",
        "SAR shadow artefacts may exist in steep terrain.",
    ],
    damage_observations=[
        "Visual verification skipped (no VLM API key or image prep failed).",
    ],
    caveats=[
        "VLM check not performed. Flood extent based on SAR raster math only.",
        "SAR C-band (Sentinel-1) can miss urban flooding due to double-bounce.",
        "Mask resolution ~10 m; sub-pixel inundation not captured.",
    ],
    confidence=0.0,
)

def _render_sar_png(data: np.ndarray, path: Path) -> Path:
    from PIL import Image
    db = 10.0 * np.log10(np.clip(data, 1e-10, None))
    db_clipped = np.clip(db, -25.0, 0.0)
    normalised = ((db_clipped + 25.0) / 25.0 * 255.0).astype(np.uint8)
    img = Image.fromarray(normalised, mode="L").convert("RGB")
    img.thumbnail((512, 512), Image.LANCZOS)
    img.save(path, format="PNG")
    return path

def _render_overlay_png(after_data: np.ndarray, flood_mask: np.ndarray, path: Path) -> Path:
    from PIL import Image
    db = 10.0 * np.log10(np.clip(after_data, 1e-10, None))
    db_clipped = np.clip(db, -25.0, 0.0)
    grey = ((db_clipped + 25.0) / 25.0 * 255.0).astype(np.uint8)
    r, g, b = grey.copy(), grey.copy(), grey.copy()
    r[flood_mask] = 220; g[flood_mask] = 30; b[flood_mask] = 30
    img = Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")
    img.thumbnail((512, 512), Image.LANCZOS)
    img.save(path, format="PNG")
    return path

def _prepare_images(event: Event):
    event_dir = DATA_DIR / event.event_id
    cache_dir = CACHE_DIR / event.event_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    before_png  = cache_dir / "before_thumb.png"
    after_png   = cache_dir / "after_thumb.png"
    overlay_png = cache_dir / "overlay_thumb.png"
    if before_png.exists() and after_png.exists() and overlay_png.exists():
        return before_png, after_png, overlay_png
    try:
        from agent.tools.raster import _read_band, get_flood_mask_array
        before_lin, _, _ = _read_band(event_dir / "before.tif")
        after_lin,  _, _ = _read_band(event_dir / "after.tif")
        flood_mask, _    = get_flood_mask_array(event)
        _render_sar_png(before_lin, before_png)
        _render_sar_png(after_lin,  after_png)
        _render_overlay_png(after_lin, flood_mask, overlay_png)
        return before_png, after_png, overlay_png
    except Exception as exc:
        log.warning("Image preparation failed (%s) - VLM will use offline stub", exc)
        return None

def run(event: Event, flood_stats: FloodStats) -> VisionCheck:
    cache_path = CACHE_DIR / event.event_id / "vision.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        log.info("vision: cache hit %s", cache_path)
        return VisionCheck.model_validate_json(cache_path.read_text())
    if not llm_available():
        log.info("vision: LLM not configured - returning offline stub")
        cache_path.write_text(_OFFLINE_VISION.model_dump_json(indent=2))
        return _OFFLINE_VISION
    imgs = _prepare_images(event)
    if imgs is None:
        log.info("vision: image prep failed - returning offline stub")
        cache_path.write_text(_OFFLINE_VISION.model_dump_json(indent=2))
        return _OFFLINE_VISION
    before_png, after_png, overlay_png = imgs
    result = vlm_json(system=_SYSTEM, user_text=_USER,
                      image_paths=[before_png, after_png, overlay_png],
                      schema=VisionCheck, temperature=0.2)
    if isinstance(result, LLMError):
        log.warning("VLM call failed: %s - using offline stub", result.error)
        cache_path.write_text(_OFFLINE_VISION.model_dump_json(indent=2))
        return _OFFLINE_VISION
    result = result.model_copy(update={"confidence": float(max(0.0, min(1.0, result.confidence)))})
    cache_path.write_text(result.model_dump_json(indent=2))
    log.info("vision: mask_plausible=%s confidence=%.2f", result.mask_plausible, result.confidence)
    return result
