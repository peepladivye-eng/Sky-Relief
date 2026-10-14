"""
Tests for Phase 6 tools: vision.py, brief.py, verify.py.
Run via WSL: ~/skyrelief_venv/bin/python -m pytest api/tests/test_tools_phase6.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest
from schemas import Event, FloodStats, VisionCheck, Weather, Priority, Exposure, Sitrep, BriefOutput

@pytest.fixture
def himachal():
    return Event(event_id="himachal_2023", name="Beas River Flood",
                 bbox=(76.85,31.65,77.25,32.05), before_date="2023-07-05",
                 after_date="2023-07-14", sensor="sentinel-1")

@pytest.fixture
def flood_stats():
    return FloodStats(area_km2=45.2, pct_of_bbox=18.5, unknown_fraction=0.0,
                      geojson={"type":"FeatureCollection","features":[]})

@pytest.fixture
def weather():
    return Weather(peak_mm=114.2, three_day_mm=301.2, anomaly=True,
                   series=[{"date":"2023-07-08","mm":114.2}])

@pytest.fixture
def priorities():
    return [
        Priority(rank=1, settlement="Larji", score=82.5,
                 reasons=["65% flooded [raster:himachal_2023]"],
                 sources=["raster:himachal_2023","hp_r02"],
                 recommended_action="Immediate evacuation required"),
        Priority(rank=2, settlement="Aut", score=65.0,
                 reasons=["30% flooded [raster:himachal_2023]"],
                 sources=["raster:himachal_2023","hp_r01"],
                 recommended_action="Road clearance or alternate route needed"),
    ]

@pytest.fixture
def exposures():
    return [
        Exposure(settlement="Larji", lat=31.826, lon=76.988,
                 flood_fraction=0.65, facilities=["hospital:CHC Larji"],
                 road_flooded=True, silent_flooded=True),
        Exposure(settlement="Aut", lat=31.874, lon=77.052,
                 flood_fraction=0.30, facilities=[],
                 road_flooded=True, silent_flooded=False),
    ]

@pytest.fixture
def offline_vision():
    return VisionCheck(mask_plausible=True,
                       false_positive_notes=["Test note"],
                       damage_observations=["Test obs"],
                       caveats=["Test caveat"], confidence=0.0)


# ── vision.py ──────────────────────────────────────────────────────────────────

class TestVision:
    def test_offline_stub_is_valid(self):
        from agent.tools.vision import _OFFLINE_VISION
        assert isinstance(_OFFLINE_VISION, VisionCheck)
        assert _OFFLINE_VISION.mask_plausible is True
        assert len(_OFFLINE_VISION.caveats) >= 1
        assert 0.0 <= _OFFLINE_VISION.confidence <= 1.0

    def test_returns_offline_when_no_api_key(self, himachal, flood_stats):
        import os; os.environ.pop("LLM_API_KEY", None)
        import importlib, config, llm
        config.LLM_API_KEY = ""
        importlib.reload(llm)
        import agent.tools.vision as vision_mod
        import cache as _  # clear cache by deleting file
        cache_f = Path("cache/himachal_2023/vision.json")
        cache_f.unlink(missing_ok=True)
        result = vision_mod.run(himachal, flood_stats)
        assert isinstance(result, VisionCheck)
        assert result.confidence == 0.0

    def test_confidence_clamped(self):
        from agent.tools.vision import _OFFLINE_VISION
        assert 0.0 <= _OFFLINE_VISION.confidence <= 1.0

    def test_render_sar_png(self, tmp_path):
        from agent.tools.vision import _render_sar_png
        import numpy as np
        data = np.random.rand(64, 64).astype(np.float32) * 0.1
        out = _render_sar_png(data, tmp_path / "test.png")
        assert out.exists()
        assert out.stat().st_size > 100

    def test_render_overlay_png(self, tmp_path):
        from agent.tools.vision import _render_overlay_png
        import numpy as np
        data = np.random.rand(64, 64).astype(np.float32) * 0.1
        mask = np.zeros((64, 64), dtype=bool)
        mask[20:40, 20:40] = True
        out = _render_overlay_png(data, mask, tmp_path / "overlay.png")
        assert out.exists()
        assert out.stat().st_size > 100


# ── brief.py ───────────────────────────────────────────────────────────────────

class TestBrief:
    def test_template_brief_returns_valid(self, himachal, flood_stats,
                                          weather, priorities, exposures):
        from agent.tools.brief import _template_brief
        b = _template_brief(himachal, flood_stats, weather, priorities, exposures)
        assert isinstance(b, BriefOutput)
        assert len(b.summary_en) > 50
        assert len(b.summary_hi) > 10
        assert len(b.whatsapp_brief_en) <= 300
        assert len(b.whatsapp_brief_hi) <= 300

    def test_template_contains_event_name(self, himachal, flood_stats,
                                           weather, priorities, exposures):
        from agent.tools.brief import _template_brief
        b = _template_brief(himachal, flood_stats, weather, priorities, exposures)
        assert "Beas" in b.summary_en or "himachal" in b.summary_en.lower()

    def test_template_contains_source_ids(self, himachal, flood_stats,
                                           weather, priorities, exposures):
        from agent.tools.brief import _template_brief
        b = _template_brief(himachal, flood_stats, weather, priorities, exposures)
        assert "raster:himachal_2023" in b.summary_en

    def test_template_mentions_silent_flooded(self, himachal, flood_stats,
                                               weather, priorities, exposures):
        from agent.tools.brief import _template_brief
        b = _template_brief(himachal, flood_stats, weather, priorities, exposures)
        assert "Larji" in b.summary_en or "silent" in b.summary_en.lower()

    def test_template_has_limitations(self, himachal, flood_stats,
                                       weather, priorities, exposures):
        from agent.tools.brief import _template_brief
        b = _template_brief(himachal, flood_stats, weather, priorities, exposures)
        assert len(b.limitations) >= 1

    def test_run_uses_cache(self, himachal, flood_stats, weather,
                             priorities, exposures, offline_vision):
        from agent.tools.brief import run
        Path("cache/himachal_2023/brief.json").unlink(missing_ok=True)
        b1 = run(himachal, flood_stats, offline_vision, weather, priorities, exposures)
        b2 = run(himachal, flood_stats, offline_vision, weather, priorities, exposures)
        assert b1.summary_en == b2.summary_en

    def test_whatsapp_brief_length(self, himachal, flood_stats,
                                    weather, priorities, exposures):
        from agent.tools.brief import _template_brief
        b = _template_brief(himachal, flood_stats, weather, priorities, exposures)
        assert len(b.whatsapp_brief_en) <= 300
        assert len(b.whatsapp_brief_hi) <= 300


# ── verify.py ──────────────────────────────────────────────────────────────────

class TestVerify:
    def test_sourced_sentence_kept(self):
        from agent.tools.verify import _verify_text
        text = "Flood covers 45 km2 [raster:himachal_2023]."
        cleaned, dropped = _verify_text(text, "test")
        assert len(dropped) == 0
        assert "45 km2" in cleaned

    def test_unsourced_sentence_dropped(self):
        from agent.tools.verify import _verify_text
        text = "The situation is improving rapidly."
        cleaned, dropped = _verify_text(text, "test")
        assert len(dropped) == 1
        assert dropped[0].startswith("The situation")

    def test_mixed_text(self):
        from agent.tools.verify import _verify_text
        text = ("Flood area 45 km2 [raster:himachal_2023]. "
                "Everything will be fine. "
                "Peak rainfall 114 mm [rainfall:himachal_2023].")
        cleaned, dropped = _verify_text(text, "test")
        assert len(dropped) == 1
        assert "Everything will be fine" in dropped[0]
        assert "raster:himachal_2023" in cleaned
        assert "rainfall:himachal_2023" in cleaned

    def test_report_id_source_valid(self):
        from agent.tools.verify import _verify_text
        text = "Larji evacuation requested [hp_r02]."
        cleaned, dropped = _verify_text(text, "test")
        assert len(dropped) == 0

    def test_live_report_id_valid(self):
        from agent.tools.verify import _verify_text
        text = "Flooding reported near bridge [live_001]."
        cleaned, dropped = _verify_text(text, "test")
        assert len(dropped) == 0

    def test_inject_and_verify_removes_injected(self):
        """Spec acceptance check: verifier removes an injected unsourced sentence."""
        from agent.tools.verify import inject_unsourced_test, run as verify_run
        from agent.tools.brief import _template_brief
        from schemas import Sitrep
        from agent.tools.weather import run as weather_run
        import os

        himachal = Event(event_id="himachal_2023", name="Beas River Flood",
                         bbox=(76.85,31.65,77.25,32.05), before_date="2023-07-05",
                         after_date="2023-07-14", sensor="sentinel-1")
        flood   = FloodStats(area_km2=45.2, pct_of_bbox=18.5, unknown_fraction=0.0,
                             geojson={"type":"FeatureCollection","features":[]})
        vision  = VisionCheck(mask_plausible=True, false_positive_notes=[],
                              damage_observations=[], caveats=[], confidence=0.7)
        weather = Weather(peak_mm=114.2, three_day_mm=301.2, anomaly=True,
                          series=[{"date":"2023-07-08","mm":114.2}])
        prios   = [Priority(rank=1, settlement="Larji", score=82.5,
                            reasons=["65% flooded [raster:himachal_2023]"],
                            sources=["raster:himachal_2023"],
                            recommended_action="Evacuate")]
        exps    = [Exposure(settlement="Larji", lat=31.826, lon=76.988,
                            flood_fraction=0.65, facilities=[],
                            road_flooded=True, silent_flooded=True)]

        Path("cache/himachal_2023/brief.json").unlink(missing_ok=True)
        brief = _template_brief(himachal, flood, weather, prios, exps)

        sitrep = Sitrep(event=himachal, flood=flood, vision=vision, weather=weather,
                        reports=[], exposures=exps, priorities=prios,
                        summary_en=brief.summary_en, summary_hi=brief.summary_hi,
                        whatsapp_brief_en=brief.whatsapp_brief_en,
                        whatsapp_brief_hi=brief.whatsapp_brief_hi,
                        limitations=brief.limitations)

        # Inject an unsourced sentence
        sitrep_with_injection = inject_unsourced_test(sitrep)
        assert "improving rapidly" in sitrep_with_injection.summary_en

        # Run verifier — must remove it
        verified, dropped = verify_run(sitrep_with_injection)
        assert "improving rapidly" not in verified.summary_en
        assert any("improving rapidly" in d for d in dropped)

    def test_empty_text_ok(self):
        from agent.tools.verify import _verify_text
        cleaned, dropped = _verify_text("", "test")
        assert cleaned == ""
        assert dropped == []

    def test_has_source_function(self):
        from agent.tools.verify import _has_source
        assert _has_source("[raster:himachal_2023]") is True
        assert _has_source("[rainfall:assam_2022]") is True
        assert _has_source("[hp_r01]") is True
        assert _has_source("[live_001]") is True
        assert _has_source("no source here") is False
