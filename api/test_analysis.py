#!/usr/bin/env python3
"""Quick test to verify analysis works without Windows security blocking."""
import sys
from pathlib import Path

# Test if rasterio can load
try:
    import rasterio
    print("✅ rasterio loaded successfully")
except Exception as e:
    print(f"❌ rasterio failed: {e}")
    sys.exit(1)

# Test basic analysis
try:
    from agent.tools import raster
    from schemas import Event
    
    # Load himachal event
    import json
    event_path = Path("../data/events/himachal_2023/meta.json")
    event = Event.model_validate_json(event_path.read_text())
    
    print(f"✅ Event loaded: {event.name}")
    print("🔄 Running raster analysis...")
    
    stats = raster.run(event)
    print(f"✅ Flood area: {stats.area_km2:.2f} km²")
    print(f"✅ Coverage: {stats.pct_of_bbox:.1f}%")
    print("✅ Analysis works!")
    
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
