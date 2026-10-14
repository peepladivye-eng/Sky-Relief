# Fix Windows Security DLL Blocking

## The Problem

Windows is blocking `hdf5.dll` (part of rasterio/GDAL) because it's an unsigned C library. This prevents the real-time flood analysis from working.

**Error:** `ImportError: DLL load failed while importing _base: An Application Control policy has blocked this file.`

---

## Solution: Unblock the DLLs

### Method 1: Allow via Windows Security Dialog

1. **Try running analysis again** from the web interface
2. **Windows Security popup will appear** (it may be behind your browser)
3. Click **"Learn more"** or **"More info"**
4. Click **"Run anyway"**
5. Refresh the page and try analysis again

---

### Method 2: Manually Unblock Python DLLs

If the popup doesn't appear or you dismissed it:

#### Step 1: Find the blocked DLL
```powershell
# In PowerShell
cd C:\Users\Lenovo\AppData\Local\Programs\Python\Python314\Lib\site-packages\rasterio
Get-ChildItem -Recurse *.dll | Select-Object FullName
```

#### Step 2: Unblock each DLL
```powershell
# Unblock all DLLs in rasterio
Get-ChildItem -Path "C:\Users\Lenovo\AppData\Local\Programs\Python\Python314\Lib\site-packages\rasterio" -Recurse -Filter *.dll | Unblock-File

# Also unblock GDAL DLLs
Get-ChildItem -Path "C:\Users\Lenovo\AppData\Local\Programs\Python\Python314\Lib\site-packages\osgeo" -Recurse -Filter *.dll | Unblock-File -ErrorAction SilentlyContinue
```

#### Step 3: Restart the API
```powershell
# Stop current process and restart
cd C:\Users\Lenovo\Desktop\Divye\NSUT\SkyRelief\api
uvicorn main:app --reload
```

---

### Method 3: Disable Windows Defender SmartScreen (Temporary)

**⚠️ Warning: Only do this for testing, re-enable after!**

1. Open **Windows Security** (search in Start menu)
2. Go to **App & browser control**
3. Click **Reputation-based protection settings**
4. Turn **OFF** "Check apps and files"
5. Restart your API server
6. Run the analysis
7. **Turn it back ON** when done

---

### Method 4: Add Python to Exclusions

1. Open **Windows Security**
2. Go to **Virus & threat protection**
3. Click **Manage settings** under "Virus & threat protection settings"
4. Scroll to **Exclusions** → Click **Add or remove exclusions**
5. Click **Add an exclusion** → **Folder**
6. Browse to: `C:\Users\Lenovo\AppData\Local\Programs\Python\Python314`
7. Restart API server

---

## Verify It's Fixed

After unblocking, test:

```powershell
# Quick test
python -c "import rasterio; print('✅ rasterio works!')"
```

If that prints "✅ rasterio works!", your analysis will work!

Then:
1. Refresh http://localhost:3000
2. Click "Run Analysis"
3. You should see the full pipeline run successfully

---

## Why We Need Real-Time Analysis

The AI analysis does:

1. **Raster processing** — Converts SAR imagery to flood masks using computer vision
2. **VLM verification** — Uses vision models to check mask plausibility
3. **LLM extraction** — Extracts structured data from news reports
4. **Geospatial fusion** — Crosses satellite data with ground reports
5. **Smart prioritization** — Ranks villages using multi-factor formula
6. **Multilingual briefs** — Generates EN/HI summaries

**Cached data** would skip all of this! We need the DLLs unblocked for real analysis.

---

## Still Having Issues?

### Alternative: Run API in WSL

From your summary, tests pass in WSL. Run there instead:

```bash
# In WSL terminal
cd /mnt/c/Users/Lenovo/Desktop/Divye/NSUT/SkyRelief/api
source ~/skyrelief_venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0
```

Windows frontend can still access it at http://localhost:8000

---

## Need Help?

Let me know which method you'd like to try, or if you see different errors!
