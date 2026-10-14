"""
Tests for Phase 4 tools: raster.py, geo.py, weather.py.
Run with: python -m pytest api/tests/test_tools_phase4.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from schemas import Event, Weather, FloodStats, Exposure


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def himachal_event():
    return Event(
        event_id="himachal_2023",
        name="Beas River Flood",
        bbox=(76.85, 31.65, 77.25, 32.05),
        before_date="2023-07-05",
        after_date="2023-07-14",
        sensor="sentinel-1",
    )

@pytest.fixture
def assam_event():
    return Event(
        event_id="assam_2022",
        name="Brahmaputra Flood",
        bbox=(92.50, 25.80, 93.30, 26.40),
        before_date="2022-06-10",
        after_date="2022-06-20",
        sensor="sentinel-1",
    )


# ── weather.py ────────────────────────────────────────────────────────────────

class TestWeather:
    def test_himachal_peak(self, himachal_event):
        from agent.tools.weather import run
        w = run(himachal_event)
        assert isinstance(w, Weather)
        assert w.peak_mm == pytest.approx(114.2)

    def test_himachal_anomaly(self, himachal_event):
        from agent.tools.weather import run
        w = run(himachal_event)
        assert w.anomaly is True

    def test_assam_peak(self, assam_event):
        from agent.tools.weather import run
        w = run(assam_event)
        assert w.peak_mm == pytest.approx(134.8)

    def test_series_length(self, himachal_event):
        from agent.tools.weather import run
        w = run(himachal_event)
        assert len(w.series) == 14
        assert all("date" in r and "mm" in r for r in w.series)

    def test_three_day_sum_correctness(self, himachal_event):
        """3-day max should be the rolling max, not just top-3 sum."""
        from agent.tools.weather import _three_day_max
        series = [{"date": "d", "mm": v} for v in [10, 20, 100, 90, 5]]
        result = _three_day_max(series)
        assert result == pytest.approx(210.0)  # 20+100+90

    def test_schema_round_trip(self, assam_event):
        from agent.tools.weather import run
        w = run(assam_event)
        w2 = Weather.model_validate_json(w.model_dump_json())
        assert w2.peak_mm == w.peak_mm


# ── raster.py helper functions ────────────────────────────────────────────────

class TestRasterHelpers:
    def test_linear_to_db(self):
        from agent.tools.raster import _linear_to_db
        # -20 dB → linear 0.01
        lin = np.array([0.01], dtype=np.float32)
        db  = _linear_to_db(lin)
        assert db[0] == pytest.approx(-20.0, abs=0.01)

    def test_linear_to_db_clip(self):
        from agent.tools.raster import _linear_to_db
        arr = np.array([0.0, -1.0], dtype=np.float32)
        db  = _linear_to_db(arr)
        assert np.all(np.isfinite(db))

    def test_pixel_area(self):
        """Use a mock affine transform so rasterio is not required."""
        from agent.tools.raster import _pixel_area_km2
        # Build a minimal affine-like object with .a and .e attributes
        class MockTransform:
            a = 0.01   # 0.01° per pixel x
            e = -0.01  # 0.01° per pixel y (negative = top-down)
        t = MockTransform()
        area = _pixel_area_km2(t, 100)
        # 100 px × (0.01 × 111.32)² ≈ 123.9 km²
        assert 0.5 < area < 500.0


# ── geo.py helper functions ───────────────────────────────────────────────────

def _shapely_available() -> bool:
    try:
        from shapely.geometry import Point  # noqa: F401
        return True
    except ImportError:
        return False


_SKIP_SHAPELY = pytest.mark.skipif(
    not _shapely_available(),
    reason="shapely DLL blocked by Application Control policy on this machine; "
           "geo tools work on the deployment server.",
)


class TestGeoHelpers:
    def test_haversine(self):
        from agent.tools.geo import _haversine_m
        # Mandi to Kullu (approx 27 km)
        d = _haversine_m(31.7090, 76.9220, 31.9579, 77.1095)
        assert 25_000 < d < 35_000

    @_SKIP_SHAPELY
    def test_buffer_wgs84(self):
        from agent.tools.geo import _buffer_wgs84
        buf = _buffer_wgs84(76.9220, 31.7090, 300.0)
        assert buf is not None
        assert buf.area > 0

    @_SKIP_SHAPELY
    def test_flood_polygon_union_empty(self):
        from agent.tools.geo import _flood_polygon_union
        fc = {"type": "FeatureCollection", "features": []}
        assert _flood_polygon_union(fc) is None

    @_SKIP_SHAPELY
    def test_flood_polygon_union_valid(self):
        from agent.tools.geo import _flood_polygon_union
        fc = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[76.9, 31.7], [76.95, 31.7],
                                     [76.95, 31.75], [76.9, 31.75],
                                     [76.9, 31.7]]]
                }
            }]
        }
        u = _flood_polygon_union(fc)
        assert u is not None
        assert u.area > 0
