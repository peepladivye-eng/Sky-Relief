# Frontend Setup Instructions

## Prerequisites
- Node.js 18+ (recommended: 20.x or 22.x)
- npm 9+ or yarn 1.22+

## Installation

### 1. Install Dependencies
```bash
cd web
npm install
```

This installs:
- Next.js 15.3 + React 18.3
- MapLibre GL 4.7
- **deck.gl 9.4** (for animated rings)
- Tailwind CSS 3.4
- TypeScript 5.7
- **Playwright 1.49** (E2E tests)
- **@axe-core/playwright 4.10** (accessibility tests)

Expected install size: ~400MB (includes Playwright browsers)

### 2. Configure Environment
```bash
cp .env.local.example .env.local  # if not already present
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Verify Installation
```bash
# Check TypeScript compilation
npm run build

# Run dev server
npm run dev
```

Open http://localhost:3000 — should see SkyRelief homepage with map.

---

## Running Tests

### E2E Tests (Playwright)
```bash
# Headless mode (CI-ready)
npm run test:e2e

# Interactive UI mode
npm run test:e2e:ui

# Headed browser (watch tests run)
npm run test:e2e:headed
```

**Note:** Tests mock API responses. For full integration:
1. Start backend: `cd ../api; uvicorn main:app --reload`
2. Remove route mocks from test files
3. Run: `npm run test:e2e`

### Linting
```bash
npm run lint
```

---

## deck.gl Animated Rings

Already configured in:
- `package.json` — dependencies added
- `components/DeckGLOverlay.tsx` — animation layer
- `components/MapView.tsx` — integration

**To verify animation works:**
1. Run analysis on `himachal_2023` event
2. Look for **pulsing purple rings** around silent-flooded villages
3. Check browser console for any WebGL errors

**Troubleshooting:**
- **"Module not found: deck.gl"** → Run `npm install` again
- **No animation visible** → Check browser supports WebGL (visit https://get.webgl.org/)
- **Animation choppy** → Check GPU acceleration enabled in browser settings

---

## Development Workflow

### Hot Reload
```bash
npm run dev
```
- Changes to `.tsx` files → instant reload
- Changes to `tailwind.config.ts` → requires page refresh
- Changes to `types.ts` → TypeScript recompiles in <1s

### Building for Production
```bash
npm run build
npm run start
```
- Creates optimized production build in `.next/`
- Static assets: ~2MB gzipped (including deck.gl)
- First load JS: ~500KB

### Type Checking (CI)
```bash
npx tsc --noEmit
```

---

## Common Issues

### Issue: `npm install` times out
**Solution:** Increase timeout:
```bash
npm install --timeout=300000
```

### Issue: Playwright browsers not installed
**Solution:** Manually install:
```bash
npx playwright install chromium firefox
```

### Issue: Map not loading
**Cause:** API not running or CORS misconfigured  
**Solution:**
1. Check backend running: `curl http://localhost:8000/health`
2. Verify `.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Check browser console for CORS errors

### Issue: TypeScript errors after updating types
**Solution:**
```bash
rm -rf .next
npm run dev
```

---

## File Structure

```
web/
├── app/
│   ├── page.tsx          # Main UI component
│   ├── types.ts          # TypeScript interfaces (matches Python schemas)
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Tailwind base + custom styles
├── components/
│   ├── MapView.tsx       # MapLibre GL map + deck.gl overlay
│   ├── DeckGLOverlay.tsx # Animated pulsing rings
│   ├── EventPicker.tsx   # Event selection dropdown
│   ├── PriorityList.tsx  # Ranked settlement cards
│   ├── TraceTimeline.tsx # Step-by-step progress
│   ├── ReportPanel.tsx   # Ground reports table
│   ├── WhatsAppBrief.tsx # Copy-to-clipboard brief
│   └── LimitationsPanel.tsx  # Caveats footer
├── e2e/
│   ├── smoke.spec.ts         # Basic UI tests
│   ├── analysis-flow.spec.ts # Mocked API interaction
│   └── accessibility.spec.ts # WCAG AA checks
├── public/               # Static assets (favicon, etc.)
├── design-system.md      # Color tokens, component patterns
├── tech.md               # Stack decisions, trade-offs
├── playwright.config.ts  # E2E test config
├── tailwind.config.ts    # Tailwind customization
├── tsconfig.json         # TypeScript strict mode
└── package.json          # Dependencies + scripts
```

---

## Next Steps

1. **Install dependencies:** `npm install`
2. **Start dev server:** `npm run dev`
3. **Run E2E tests:** `npm run test:e2e`
4. **Check design system:** Read `design-system.md`
5. **Verify deck.gl:** Look for purple rings after analysis

**Ready to proceed with Phase 6 backend tools (vision.py, brief.py, verify.py).**
