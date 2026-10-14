import sys
print("Python:", sys.version)
packages = ["rasterio", "shapely", "pyproj", "numpy", "scipy", "skimage", "fastapi", "pydantic", "PIL"]
for pkg in packages:
    try:
        m = __import__(pkg)
        v = getattr(m, "__version__", "ok")
        print(f"  OK  {pkg} {v}")
    except Exception as e:
        print(f"  FAIL {pkg}: {e}")
print("Done")
