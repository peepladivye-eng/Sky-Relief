"""
Tests for Phase 5 tools: reports.py, fuse.py, prioritize.py.
Run with: python -m pytest api/tests/test_tools_phase5.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from schemas import Event, Report, Exposure, Weather, FloodStats


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def himachal():
    return Event(
        event_id="himachal_2023",
        name="Beas River Flood",
        bbox=(76.85, 31.65, 77.25, 32.05),
        before_date="2023-07-05",
        after_date="2023-07-14",
        sensor="sentinel-1",
    )

@pytest.fixture
def assam():
    return Event(
        event_id="assam_2022",
        name="Brahmaputra Flood",
        bbox=(92.50, 25.80, 93.30, 26.40),
        before_date="2022-06-10",
        after_date="2022-06-20",
        sensor="sentinel-1",
    )

@pytest.fixture
def empty_flood_stats():
    return FloodStats(
        area_km2=0.0, pct_of_bbox=0.0, unknown_fraction=0.0,
        geojson={"type": "FeatureCollection", "features": []},
    )

@pytest.fixture
def sample_flood_stats():
    """A flood polygon that covers Larji village (76.988, 31.826)."""
    return FloodStats(
        area_km2=12.5, pct_of_bbox=8.2, unknown_fraction=0.0,
        geojson={
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"flood": True},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[76.95, 31.80], [77.05, 31.80],
                                     [77.05, 31.87], [76.95, 31.87],
                                     [76.95, 31.80]]]
                }
            }]
        }
    )

@pytest.fixture
def sample_exposures():
    return [
        Exposure(settlement="Larji",     lat=31.826, lon=76.988,
                 flood_fraction=0.65, facilities=["hospital:CHC Larji"],
                 road_flooded=True,  silent_flooded=True),
        Exposure(settlement="Aut",       lat=31.874, lon=77.052,
                 flood_fraction=0.30, facilities=[],
                 road_flooded=True,  silent_flooded=False),
        Exposure(settlement="Mandi",     lat=31.709, lon=76.922,
                 flood_fraction=0.05, facilities=["hospital:Zonal Hospital Mandi"],
                 road_flooded=False, silent_flooded=False),
        Exposure(settlement="Sundernagar", lat=31.535, lon=76.899,
                 flood_fraction=0.0,  facilities=[],
                 road_flooded=False, silent_flooded=False),
    ]

@pytest.fixture
def sample_reports():
    return [
        Report(id="hp_r01", text="NH-3 blocked near Aut", source="news",
               source_url=None, place="Aut", lat=31.874, lon=77.052,
               need="road clearance", urgency=3, count=None, status=None),
        Report(id="hp_r02", text="Larji submerged, evacuation needed", source="news",
               source_url=None, place="Larji", lat=31.826, lon=76.988,
               need="evacuation", urgency=3, count=200, status=None),
        Report(id="hp_r07", text="Sundernagar manageable", source="news",
               source_url=None, place="Sundernagar", lat=31.535, lon=76.899,
               need="food", urgency=1, count=200, status=None),
    ]

@pytest.fixture
def sample_weather():
    return Weather(
        peak_mm=114.2, three_day_mm=301.2, anomaly=True,
        series=[{"date": "2023-07-08", "mm": 114.2}],
    )


# ── reports.py ────────────────────────────────────────────────────────────────

class TestReports:
    def test_loads_fixture_reports(self, himachal):
        from agent.tools.reports import run
        reports = run(himachal)
        assert len(reports) >= 10
        assert all(isinstance(r, Report) for r in reports)

    def test_all_have_id_and_text(self, himachal):
        from agent.tools.reports import run
        reports = run(himachal)
        for r in reports:
            assert r.id
            assert r.text

    def test_geocoded_from_fixture(self, himachal):
        from agent.tools.reports import run
        reports = run(himachal)
        with_coords = [r for r in reports if r.lat is not None]
        assert len(with_coords) >= 8, "Most fixture reports should have coordinates"

    def test_urgency_in_range(self, himachal):
        from agent.tools.reports import run
        reports = run(himachal)
        for r in reports:
            if r.urgency is not None:
                assert 1 <= r.urgency <= 3

    def test_extra_reports_merged(self, himachal):
        from agent.tools.reports import run
        reports = run(himachal, extra_texts=["Flooding in Larji, urgent rescue needed"])
        live = [r for r in reports if r.source == "live_input"]
        assert len(live) == 1
        assert live[0].id == "live_001"

    def test_heuristic_urgency_high(self):
        from agent.tools.reports import _heuristic_extract
        r = _heuristic_extract("Village submerged, immediate rescue required, people missing")
        assert r.urgency == 3

    def test_heuristic_urgency_low(self):
        from agent.tools.reports import _heuristic_extract
        r = _heuristic_extract("Situation improving, relief camp distributed food")
        assert r.urgency == 1

    def test_heuristic_count(self):
        from agent.tools.reports import _heuristic_extract
        r = _heuristic_extract("Around 500 families affected by flood")
        assert r.count == 500

    def test_geocoder_partial_match(self, himachal):
        from agent.tools.reports import _build_gazetteer, _geocode
        from pathlib import Path
        gaz = _build_gazetteer(Path("data/events/himachal_2023"))
        lat, lon = _geocode("Mandi", gaz)
        assert lat is not None
        assert 31.5 < lat < 32.0

    def test_assam_fixture(self, assam):
        from agent.tools.reports import run
        reports = run(assam)
        assert len(reports) >= 11


# ── fuse.py ───────────────────────────────────────────────────────────────────

class TestFuse:
    def test_all_reports_get_status(self, himachal, sample_reports,
                                    sample_flood_stats, sample_exposures):
        from agent.tools.fuse import run
        fused_r, _ = run(himachal, sample_reports, sample_flood_stats, sample_exposures)
        assert all(r.status is not None for r in fused_r)

    def test_status_values_valid(self, himachal, sample_reports,
                                 sample_flood_stats, sample_exposures):
        from agent.tools.fuse import run
        fused_r, _ = run(himachal, sample_reports, sample_flood_stats, sample_exposures)
        valid = {"confirmed", "contradicted", "unverified"}
        for r in fused_r:
            assert r.status in valid

    def test_no_coords_is_unverified(self, himachal, empty_flood_stats, sample_exposures):
        from agent.tools.fuse import run
        import os
        cache = "cache/himachal_2023/fused.json"
        if os.path.exists(cache):
            os.remove(cache)
        no_coord = Report(id="x1", text="Some report", source="test",
                          source_url=None, place=None, lat=None, lon=None,
                          need=None, urgency=None, count=None, status=None)
        fused_r, _ = run(himachal, [no_coord], empty_flood_stats, sample_exposures)
        assert fused_r[0].status == "unverified"

    def test_silent_flooded_present(self, himachal, sample_flood_stats, sample_exposures):
        """Larji has flood_fraction=0.65; pass a report far away (>900m) — must be silent."""
        from agent.tools.fuse import run
        import os
        cache = "cache/himachal_2023/fused.json"
        if os.path.exists(cache):
            os.remove(cache)
        # Report is near Bhuntar (77.168, 31.878) — far from Larji (76.988, 31.826)
        reports = [
            Report(id="r_far", text="Bhuntar airport flooded", source="news",
                   source_url=None, place="Bhuntar", lat=31.878, lon=77.168,
                   need="helicopter", urgency=2, count=None, status=None),
        ]
        _, fused_e = run(himachal, reports, sample_flood_stats, sample_exposures)
        larji = next(e for e in fused_e if e.settlement == "Larji")
        assert larji.silent_flooded is True

    def test_far_report_contradicted(self, himachal, empty_flood_stats, sample_exposures):
        """A report far from any flood pixel should be contradicted."""
        from agent.tools.fuse import run
        far_report = Report(
            id="far1", text="Flooding in some distant area", source="test",
            source_url=None, place="Faraway", lat=30.0, lon=75.0,
            need=None, urgency=1, count=None, status=None,
        )
        fused_r, _ = run(himachal, [far_report], empty_flood_stats, sample_exposures)
        # No flood pixels → all reports should be contradicted (infinite distance)
        assert fused_r[0].status == "contradicted"

    def test_returns_same_count(self, himachal, sample_reports,
                                sample_flood_stats, sample_exposures):
        import os
        cache = "cache/himachal_2023/fused.json"
        if os.path.exists(cache):
            os.remove(cache)
        from agent.tools.fuse import run
        fused_r, fused_e = run(himachal, sample_reports, sample_flood_stats, sample_exposures)
        assert len(fused_r) == len(sample_reports)
        assert len(fused_e) == len(sample_exposures)


# ── prioritize.py ─────────────────────────────────────────────────────────────

def _clear_priority_cache():
    import os
    for path in ["cache/himachal_2023/priorities.json",
                 "cache/assam_2022/priorities.json"]:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


class TestPrioritize:
    def test_returns_priority_list(self, himachal, sample_exposures,
                                   sample_reports, sample_weather):
        _clear_priority_cache()
        from agent.tools.prioritize import run
        # Assign statuses first
        reports_with_status = [
            r.model_copy(update={"status": "confirmed"}) for r in sample_reports
        ]
        plist = run(himachal, sample_exposures, reports_with_status, sample_weather)
        assert len(plist) == len(sample_exposures)
        assert all(p.rank >= 1 for p in plist)

    def test_ranks_are_sequential(self, himachal, sample_exposures,
                                  sample_reports, sample_weather):
        _clear_priority_cache()
        from agent.tools.prioritize import run
        reports_ws = [r.model_copy(update={"status": "confirmed"}) for r in sample_reports]
        plist = run(himachal, sample_exposures, reports_ws, sample_weather)
        ranks = [p.rank for p in plist]
        assert ranks == list(range(1, len(plist) + 1))

    def test_scores_descending(self, himachal, sample_exposures,
                               sample_reports, sample_weather):
        _clear_priority_cache()
        from agent.tools.prioritize import run
        reports_ws = [r.model_copy(update={"status": "confirmed"}) for r in sample_reports]
        plist = run(himachal, sample_exposures, reports_ws, sample_weather)
        scores = [p.score for p in plist]
        assert scores == sorted(scores, reverse=True)

    def test_larji_ranks_high(self, himachal, sample_exposures,
                              sample_reports, sample_weather):
        """Larji: flood_fraction=0.65, hospital, road_flooded, silent_flooded → top rank."""
        _clear_priority_cache()
        from agent.tools.prioritize import run
        # Give Larji a confirmed report too
        reports_ws = [r.model_copy(update={"status": "confirmed"}) for r in sample_reports]
        plist = run(himachal, sample_exposures, reports_ws, sample_weather)
        larji = next(p for p in plist if p.settlement == "Larji")
        assert larji.rank <= 2

    def test_sundernagar_ranks_low(self, himachal, sample_exposures,
                                   sample_reports, sample_weather):
        """Sundernagar: flood_fraction=0 → lowest score."""
        _clear_priority_cache()
        from agent.tools.prioritize import run
        reports_ws = [r.model_copy(update={"status": "confirmed"}) for r in sample_reports]
        plist = run(himachal, sample_exposures, reports_ws, sample_weather)
        snagar = next(p for p in plist if p.settlement == "Sundernagar")
        assert snagar.rank == len(plist)

    def test_reasons_non_empty(self, himachal, sample_exposures,
                               sample_reports, sample_weather):
        _clear_priority_cache()
        from agent.tools.prioritize import run
        reports_ws = [r.model_copy(update={"status": "confirmed"}) for r in sample_reports]
        plist = run(himachal, sample_exposures, reports_ws, sample_weather)
        for p in plist:
            assert len(p.reasons) >= 1

    def test_sources_present(self, himachal, sample_exposures,
                             sample_reports, sample_weather):
        _clear_priority_cache()
        from agent.tools.prioritize import run
        reports_ws = [r.model_copy(update={"status": "confirmed"}) for r in sample_reports]
        plist = run(himachal, sample_exposures, reports_ws, sample_weather)
        for p in plist:
            assert len(p.sources) >= 1

    def test_score_bounds(self, himachal, sample_exposures,
                          sample_reports, sample_weather):
        _clear_priority_cache()
        from agent.tools.prioritize import run
        reports_ws = [r.model_copy(update={"status": "confirmed"}) for r in sample_reports]
        plist = run(himachal, sample_exposures, reports_ws, sample_weather)
        for p in plist:
            assert 0.0 <= p.score <= 100.0

    def test_recommended_action_mapping(self):
        from agent.tools.prioritize import _recommended_action
        assert "evacuation" in _recommended_action(["evacuation"]).lower()
        assert "medical" in _recommended_action(["medical supplies"]).lower()
        assert "food" in _recommended_action(["food", "water"]).lower()

    def test_silent_flooded_boosts_score(self, himachal, sample_weather):
        """Silent-flooded settlement should score exactly W_SILENT_FLOODED points higher."""
        import os
        cache = "cache/himachal_2023/priorities.json"
        if os.path.exists(cache):
            os.remove(cache)
        from agent.tools.prioritize import run
        base_exp   = Exposure(settlement="TestVillage",   lat=31.8, lon=77.0,
                              flood_fraction=0.5, facilities=[],
                              road_flooded=False, silent_flooded=False)
        silent_exp = Exposure(settlement="SilentVillage", lat=31.85, lon=77.05,
                              flood_fraction=0.5, facilities=[],
                              road_flooded=False, silent_flooded=True)
        plist = run(himachal, [base_exp, silent_exp], [], sample_weather)
        scores = {p.settlement: p.score for p in plist}
        assert "SilentVillage" in scores, f"Got settlements: {list(scores.keys())}"
        diff = scores["SilentVillage"] - scores["TestVillage"]
        from config import W_SILENT_FLOODED
        assert abs(diff - W_SILENT_FLOODED) < 0.01
