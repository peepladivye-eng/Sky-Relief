"""
SkyRelief — central configuration.
All tunable constants live here so they can be documented and adjusted per-event.
"""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).parent.parent
DATA_DIR   = ROOT_DIR / "data" / "events"
CACHE_DIR  = ROOT_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── LLM / VLM ─────────────────────────────────────────────────────────────────
LLM_BASE_URL : str = os.getenv("LLM_BASE_URL", "https://api.studio.nebius.ai/v1")
LLM_API_KEY  : str = os.getenv("LLM_API_KEY", "")
LLM_MODEL    : str = os.getenv("LLM_MODEL",   "meta-llama/Meta-Llama-3.1-70B-Instruct")
VLM_MODEL    : str = os.getenv("VLM_MODEL",   "Qwen/Qwen2-VL-72B-Instruct")

# ── Live data toggle ──────────────────────────────────────────────────────────
LIVE_DATA: bool = os.getenv("LIVE_DATA", "0") == "1"

# ── Raster thresholds ─────────────────────────────────────────────────────────
# Sentinel-1 VV (dB) water threshold; can be overridden per-event in meta.json
SAR_WATER_DB_DEFAULT: float = -16.0
# Minimum change (dB) required to call a pixel newly flooded
SAR_CHANGE_DB: float = -3.0
# Remove blobs smaller than this (pixels)
MIN_BLOB_PIXELS: int = 20
# Slope threshold for shadow masking (degrees); only applied if slope.tif present
SLOPE_SHADOW_DEG: float = 15.0
# Sentinel-2 NDWI threshold
S2_NDWI_THRESHOLD: float = 0.1

# ── Geo exposure ──────────────────────────────────────────────────────────────
# Buffer radius around settlement point (metres) for flood-fraction calculation
SETTLEMENT_BUFFER_M: float = 300.0
# Report location matched to flood mask within this radius (metres) → confirmed
CONFIRM_RADIUS_M: float = 500.0
# Report location farther than this from any flood pixel → contradicted
CONTRADICT_RADIUS_M: float = 2000.0

# ── Priority score weights (must sum to 100) ─────────────────────────────────
# See README §7 for rationale.
W_FLOOD_FRACTION   : float = 40.0   # flood coverage of 300 m buffer
W_REPORT_URGENCY   : float = 20.0   # normalised sum of report urgency scores
W_SILENT_FLOODED   : float = 15.0   # flooded with zero ground reports
W_FACILITIES       : float = 10.0   # hospitals/schools/bridges exposed
W_ROAD_CUT         : float = 10.0   # access road flooded
W_RAIN_ANOMALY     : float =  5.0   # rainfall anomaly flag

assert (W_FLOOD_FRACTION + W_REPORT_URGENCY + W_SILENT_FLOODED
        + W_FACILITIES + W_ROAD_CUT + W_RAIN_ANOMALY) == 100.0, \
    "Priority weights must sum to 100"

# ── LLM retry ─────────────────────────────────────────────────────────────────
LLM_MAX_RETRIES: int = 1

# ── Misc ──────────────────────────────────────────────────────────────────────
API_VERSION: str = "1.0.0"
