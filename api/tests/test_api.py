"""
test_api.py - Phase 7 integration tests
Tests FastAPI endpoints without running the full agent loop.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client():
    from main import app
    return TestClient(app)

class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_has_version(self, client):
        r = client.get("/health")
        assert "version" in r.json()

class TestEvents:
    def test_events_returns_list(self, client):
        r = client.get("/events")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_events_has_both_events(self, client):
        r = client.get("/events")
        ids = [e["event_id"] for e in r.json()]
        assert "himachal_2023" in ids
        assert "assam_2022" in ids

    def test_event_schema_valid(self, client):
        r = client.get("/events")
        for ev in r.json():
            assert "event_id" in ev
            assert "name" in ev
            assert "bbox" in ev
            assert "sensor" in ev
            assert len(ev["bbox"]) == 4

class TestLayers:
    def test_invalid_layer_400(self, client):
        r = client.get("/layers/himachal_2023/invalid_layer")
        assert r.status_code == 400

    def test_unknown_event_404(self, client):
        r = client.get("/layers/nonexistent_event/before")
        assert r.status_code == 404

    def test_flood_layer_before_analyze_404(self, client):
        import os
        cache_f = Path("cache/himachal_2023/flood_stats.json")
        cache_f.unlink(missing_ok=True)
        r = client.get("/layers/himachal_2023/flood")
        assert r.status_code == 404

class TestExport:
    def test_export_before_analyze_404(self, client):
        cache_f = Path("cache/himachal_2023/brief.json")
        cache_f.unlink(missing_ok=True)
        r = client.get("/export/himachal_2023.md")
        assert r.status_code == 404

class TestOrchestrator:
    def test_orchestrator_imports(self):
        from agent.orchestrator import run_analysis
        assert callable(run_analysis)

    def test_invalid_event_yields_error(self):
        import asyncio
        from agent.orchestrator import run_analysis
        async def collect():
            msgs = []
            async for m in run_analysis("nonexistent_event_xyz"):
                msgs.append(m)
            return msgs
        msgs = asyncio.run(collect())
        assert any(m.get("type") == "error" for m in msgs)