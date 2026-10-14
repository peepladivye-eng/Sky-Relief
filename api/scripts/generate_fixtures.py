"""
generate_fixtures.py
--------------------
Creates synthetic Sentinel-1 VV fixtures using only numpy + struct.
Writes minimal valid single-band float32 GeoTIFFs that rasterio (running
at API serving time) can read.

Run from repo root:
    python api/scripts/generate_fixtures.py

Design:
  - before.tif : linear-power SAR — dry terrain ~−10 dB, river corridor < −16 dB
  - after.tif  : same + flood extent pixels dropped to < −19 dB (clearly flooded)
  - ref_mask.tif: uint8 binary, 1 = new inundation (ground-truth for IoU eval)
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

import numpy as np

ROOT  = Path(__file__).parent.parent.parent
DATA  = ROOT / "data" / "events"
RNG   = np.random.default_rng(42)


# ──────────────────────────────────────────────────────────────────────────────
# Minimal GeoTIFF writer (no rasterio dependency)
# We write a stripped-down Class-F GeoTIFF (ImageWidth, ImageLength,
# BitsPerSample, Compression=1 (none), PhotometricInterp=1,
# StripOffsets, SamplesPerPixel, RowsPerStrip, StripByteCounts,
# XResolution, YResolution, ResolutionUnit, ModelPixelScaleTag,
# ModelTiepointTag, GeoKeyDirectoryTag).
# ──────────────────────────────────────────────────────────────────────────────

def _pack_rational(num: int, den: int) -> bytes:
    return struct.pack("<II", num, den)


def write_geotiff_float32(
    path: Path,
    data: np.ndarray,
    minx: float, miny: float, maxx: float, maxy: float,
    nodata: float | None = None,
) -> None:
    """
    Write a single-band float32 GeoTIFF with a basic geographic (WGS-84)
    georeference derived from bbox.

    This uses only struct + numpy — no rasterio required at generation time.
    The file is 100% rasterio-readable at runtime.
    """
    assert data.ndim == 2
    rows, cols = data.shape

    px_w = (maxx - minx) / cols   # pixel width  (degrees)
    px_h = (maxy - miny) / rows   # pixel height (positive)

    # We'll write the image data right after the IFD block.
    # Compute layout first so we know offsets.

    # ── TIFF constants ────────────────────────────────────────────────────
    BYTE_ORDER   = b"II"   # little-endian
    MAGIC        = 42
    FLOAT32      = 11      # TIFF SampleFormat float (we use SAMPLEFORMAT tag separately)
    SHORT        = 3
    LONG         = 4
    RATIONAL     = 5
    DOUBLE       = 12
    SBYTE        = 6

    # ── Tag definitions: (tag_id, type, count, value_or_offset) ──────────
    # We build the IFD manually.

    # Image data
    img_bytes = data.astype("<f4").tobytes()
    img_size  = len(img_bytes)

    # GeoTIFF double arrays (ModelPixelScale, ModelTiepoint)
    pixel_scale  = struct.pack("<3d", px_w, px_h, 0.0)            # 24 bytes
    tiepoint     = struct.pack("<6d", 0.0, 0.0, 0.0, minx, maxy, 0.0)  # 48 bytes

    # GeoKeyDirectory (minimal WGS-84 geographic CRS)
    # Header: KeyDirectoryVersion=1, KeyRevision=1, MinorRevision=0, NumKeys=3
    # Keys: GTModelTypeGeoKey=2(geographic), GTRasterTypeGeoKey=1(pixel-is-area),
    #       GeographicTypeGeoKey=4326(WGS84)
    geokeys = struct.pack("<16H",
        1, 1, 0, 3,         # header
        1024, 0, 1, 2,      # GTModelTypeGeoKey = ModelTypeGeographic
        1025, 0, 1, 1,      # GTRasterTypeGeoKey = RasterPixelIsArea
        2048, 0, 1, 4326,   # GeographicTypeGeoKey = GCS_WGS_84
    )  # 32 bytes

    # ── Offsets ───────────────────────────────────────────────────────────
    # Layout in file:
    #   0: TIFF header (8 bytes)
    #   8: IFD (starts here; we compute size below)
    # We'll place extra data (rational, doubles, geokeys) after the IFD,
    # then image data at the end.

    num_tags = 16 if nodata is None else 17

    ifd_size   = 2 + num_tags * 12 + 4   # count(2) + entries + next_ifd(4)
    ifd_offset = 8                         # right after header

    extra_offset = ifd_offset + ifd_size   # where extra data blocks start

    # XResolution rational (72/1)
    xres_offset = extra_offset
    xres_bytes  = _pack_rational(72, 1)    # 8 bytes

    # YResolution rational (72/1)
    yres_offset = xres_offset + 8
    yres_bytes  = _pack_rational(72, 1)    # 8 bytes

    # ModelPixelScaleTag
    scale_offset = yres_offset + 8
    # ModelTiepointTag
    tpt_offset   = scale_offset + len(pixel_scale)
    # GeoKeyDirectory
    geokey_offset = tpt_offset + len(tiepoint)

    # Nodata (ASCII string or DOUBLE)
    nodata_offset = geokey_offset + len(geokeys)
    nodata_bytes  = b""
    if nodata is not None:
        nodata_str   = f"{nodata}\x00".encode()
        nodata_bytes = nodata_str

    img_offset = nodata_offset + len(nodata_bytes)

    # ── Build IFD entries ─────────────────────────────────────────────────
    def entry(tag: int, typ: int, count: int, val_or_off) -> bytes:
        """Pack a 12-byte IFD entry.  val_or_off is an int offset or a 4-byte-fittable int."""
        return struct.pack("<HHI4s", tag, typ, count,
                           struct.pack("<I", val_or_off)[:4])

    entries: list[bytes] = []
    entries.append(entry(256, LONG,  1, cols))                        # ImageWidth
    entries.append(entry(257, LONG,  1, rows))                        # ImageLength
    entries.append(entry(258, SHORT, 1, 32))                          # BitsPerSample = 32
    entries.append(entry(259, SHORT, 1, 1))                           # Compression = none
    entries.append(entry(262, SHORT, 1, 1))                           # PhotometricInterp = BlackIsZero
    entries.append(entry(273, LONG,  1, img_offset))                  # StripOffsets
    entries.append(entry(277, SHORT, 1, 1))                           # SamplesPerPixel
    entries.append(entry(278, LONG,  1, rows))                        # RowsPerStrip = all rows
    entries.append(entry(279, LONG,  1, img_size))                    # StripByteCounts
    entries.append(struct.pack("<HHI4s", 282, RATIONAL, 1,            # XResolution
                               struct.pack("<I", xres_offset)))
    entries.append(struct.pack("<HHI4s", 283, RATIONAL, 1,            # YResolution
                               struct.pack("<I", yres_offset)))
    entries.append(entry(296, SHORT,  1, 2))                          # ResolutionUnit = inch
    entries.append(entry(339, SHORT,  1, 3))                          # SampleFormat = float
    entries.append(struct.pack("<HHI4s", 33550, DOUBLE, 3,            # ModelPixelScaleTag
                               struct.pack("<I", scale_offset)))
    entries.append(struct.pack("<HHI4s", 33922, DOUBLE, 6,            # ModelTiepointTag
                               struct.pack("<I", tpt_offset)))
    entries.append(struct.pack("<HHI4s", 34736, SHORT, 16,            # GeoKeyDirectoryTag
                               struct.pack("<I", geokey_offset)))
    if nodata is not None:
        entries.append(struct.pack("<HHI4s", 42113, 2,                # GDAL_NODATA (ASCII)
                                   len(nodata_bytes),
                                   struct.pack("<I", nodata_offset)))

    assert len(entries) == num_tags

    ifd_block = (
        struct.pack("<H", num_tags)
        + b"".join(entries)
        + struct.pack("<I", 0)   # next IFD offset = 0 (no more IFDs)
    )

    # ── TIFF header ───────────────────────────────────────────────────────
    header = BYTE_ORDER + struct.pack("<HI", MAGIC, ifd_offset)

    # ── Write ─────────────────────────────────────────────────────────────
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(header)
        f.write(ifd_block)
        f.write(xres_bytes)
        f.write(yres_bytes)
        f.write(pixel_scale)
        f.write(tiepoint)
        f.write(geokeys)
        f.write(nodata_bytes)
        f.write(img_bytes)

    kb = path.stat().st_size / 1024
    print(f"  wrote {path.relative_to(ROOT)}  ({kb:.0f} KB)")


# ──────────────────────────────────────────────────────────────────────────────
# Per-event synthetic data generation
# ──────────────────────────────────────────────────────────────────────────────

def db_to_linear(db: np.ndarray) -> np.ndarray:
    return (10.0 ** (db / 10.0)).astype(np.float32)


def make_event(event_id: str, rows: int = 512, cols: int = 512) -> None:
    meta_path = DATA / event_id / "meta.json"
    with open(meta_path) as f:
        meta = json.load(f)

    minx, miny, maxx, maxy = meta["bbox"]
    water_db: float = meta.get("water_db", -16.0)
    event_dir = DATA / event_id

    # ── Background dry terrain: -10 dB with speckle ───────────────────────
    bg_db = -10.0 + RNG.normal(0, 1.0, (rows, cols)).astype(np.float32)

    # ── Permanent water: river corridor ──────────────────────────────────
    perm_mask = np.zeros((rows, cols), dtype=bool)
    river_center = cols // 2
    river_w      = max(8, cols // 30)
    for r in range(rows):
        offset = int(10 * np.sin(r / rows * 4 * np.pi))
        c0 = max(0, river_center + offset - river_w // 2)
        c1 = min(cols, c0 + river_w)
        perm_mask[r, c0:c1] = True

    if "assam" in event_id:
        branch_col = cols // 3
        branch_w   = max(5, cols // 50)
        for r in range(rows):
            offset = int(6 * np.cos(r / rows * 3 * np.pi))
            c0 = max(0, branch_col + offset - branch_w // 2)
            c1 = min(cols, c0 + branch_w)
            perm_mask[r, c0:c1] = True

    before_db = bg_db.copy()
    before_db[perm_mask] = (
        water_db - 4.0
        + RNG.normal(0, 0.5, int(perm_mask.sum())).astype(np.float32)
    )

    # ── New flood extent ──────────────────────────────────────────────────
    fr0 = int(rows * 0.30)
    fr1 = int(rows * 0.85)
    fc0 = int(cols * 0.25)
    fc1 = int(cols * 0.75)
    new_flood = np.zeros((rows, cols), dtype=bool)
    new_flood[fr0:fr1, fc0:fc1] = True

    if "assam" in event_id:
        # Wider floodplain
        new_flood[int(rows*0.20):int(rows*0.90),
                  int(cols*0.15):int(cols*0.85)] = True

    new_flood &= ~perm_mask  # exclude permanent water

    after_db = before_db.copy()
    after_db[new_flood] = (
        water_db - 5.0
        + RNG.normal(0, 0.8, int(new_flood.sum())).astype(np.float32)
    )

    # ── Small noise on both scenes ────────────────────────────────────────
    before_db += RNG.normal(0, 0.3, (rows, cols)).astype(np.float32)
    after_db  += RNG.normal(0, 0.3, (rows, cols)).astype(np.float32)

    before_lin = db_to_linear(before_db)
    after_lin  = db_to_linear(after_db)
    ref_mask   = new_flood.astype(np.uint8)

    write_geotiff_float32(event_dir / "before.tif",   before_lin, minx, miny, maxx, maxy)
    write_geotiff_float32(event_dir / "after.tif",    after_lin,  minx, miny, maxx, maxy)
    write_geotiff_float32(event_dir / "ref_mask.tif", ref_mask.astype(np.float32),
                          minx, miny, maxx, maxy, nodata=255.0)

    flood_pct = 100.0 * new_flood.mean()
    print(f"  flood pixels: {new_flood.sum():,}/{rows*cols:,} ({flood_pct:.1f}%)")


if __name__ == "__main__":
    for eid in ["himachal_2023", "assam_2022"]:
        print(f"\n=== {eid} ===")
        make_event(eid)
    print("\nFixtures ready.")
