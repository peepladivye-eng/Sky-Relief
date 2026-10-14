# Final Fix for Windows DLL Blocking

The issue is that Windows Application Control Policy is blocking rasterio DLLs **at the kernel level**, not just file properties. `Unblock-File` alone won't fix this.

---

## ✅ **SOLUTION 1: Run as Administrator (Quickest)**

### Step 1: Stop both servers
Let me stop them for you.

### Step 2: Open PowerShell as Administrator
1. Press `Win + X`
2. Click **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**

### Step 3: Start API as Admin
```powershell
cd C:\Users\Lenovo\Desktop\Divye\NSUT\SkyRelief\api
uvicorn main:app --reload
```

### Step 4: Start Frontend (in another admin PowerShell)
```powershell
cd C:\Users\Lenovo\Desktop\Divye\NSUT\SkyRelief\web
npm run dev
```

Admin privileges bypass Application Control Policy.

---

## ✅ **SOLUTION 2: Use WSL (Most Reliable)**

From your summary: "70 passing tests (WSL, 0 skips)" — **it already works there!**

### In WSL Terminal:

```bash
# Start API
cd /mnt/c/Users/Lenovo/Desktop/Divye/NSUT/SkyRelief/api
source ~/skyrelief_venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0
```

### In Windows PowerShell:

```powershell
# Start frontend
cd C:\Users\Lenovo\Desktop\Divye\NSUT\SkyRelief\web
npm run dev
```

Frontend on Windows → API on WSL → works perfectly!

---

## ✅ **SOLUTION 3: Disable Application Control**

**⚠️ Requires Admin or IT approval**

### Option A: Group Policy (Admin required)

1. Press `Win + R`, type `gpedit.msc`
2. Navigate to:
   ```
   Computer Configuration
   → Administrative Templates
   → Windows Components  
   → Windows Defender Application Control
   ```
3. Find **"Configure the Application Identity service"**
4. Set to **Disabled**
5. Restart computer

### Option B: Registry (Dangerous - backup first!)

```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy" -Name "VerifiedAndReputablePolicyState" -Value 0 -PropertyType DWORD -Force
Restart-Computer
```

---

## ✅ **SOLUTION 4: Sign the DLLs (Advanced)**

This requires a code signing certificate (not practical for testing).

---

## 🎯 **RECOMMENDED: Try Solution 1 or 2**

### Which should you use?

- **Solution 1 (Admin mode)**: Fastest if you have admin rights
- **Solution 2 (WSL)**: Most reliable, already tested working
- **Solution 3**: Only if you have IT approval
- **Solution 4**: Not practical

---

## Let Me Help

Would you like me to:

**A)** Stop the current servers so you can restart them as Administrator?

**B)** Guide you through WSL setup (API in WSL, frontend in Windows)?

**C)** Create a mock mode for demo purposes (limited functionality)?

Let me know which option works best for you!
