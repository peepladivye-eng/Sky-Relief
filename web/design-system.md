# SkyRelief Design System

## Color Tokens

### Semantic Colors
- **Primary**: Blue (`#3b82f6`) — analysis actions, flood visualization
- **Secondary**: Orange (`#f97316`) — paste report, medium priority
- **Accent**: Purple (`#a855f7`) — silent-flooded settlements
- **Success**: Green (`#22c55e`) — completed steps
- **Warning**: Yellow (`#eab308`) — low priority settlements
- **Danger**: Red (`#ef4444`) — high priority settlements, errors

### Grayscale (Dark Theme)
- **bg-base**: `#030712` (gray-950) — main background
- **bg-surface**: `#111827` (gray-900) — cards, sidebars
- **bg-overlay**: `#1f2937` (gray-800) — inputs, hover states
- **border**: `#374151` (gray-700) — dividers
- **text-primary**: `#f9fafb` (gray-50) — headings, body
- **text-secondary**: `#9ca3af` (gray-400) — labels, metadata

## Typography

### Font Stack
- **Sans**: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
- **Mono**: "Courier New", monospace (for report timestamps, IDs)

### Scales
- **xs**: 0.75rem / 12px
- **sm**: 0.875rem / 14px
- **base**: 1rem / 16px
- **lg**: 1.125rem / 18px
- **xl**: 1.25rem / 20px
- **2xl**: 1.5rem / 24px

## Spacing
Use Tailwind's default scale: 0.25rem increments (1 = 4px, 2 = 8px, 3 = 12px, 4 = 16px, etc.)

## Components

### Buttons
```tsx
// Primary action
className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"

// Secondary action
className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-700 text-white font-medium py-1.5 px-3 rounded-lg transition-colors"

// Ghost button
className="text-gray-400 hover:text-white hover:bg-gray-800 py-1.5 px-3 rounded-lg transition-colors"
```

### Cards
```tsx
className="bg-gray-900 border border-gray-800 rounded-xl p-4 shadow-lg"
```

### Inputs
```tsx
className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500"
```

### Priority Settlement Circle Colors
- **High (≥70)**: `#ef4444` (red-500)
- **Medium (45-69)**: `#f97316` (orange-500)
- **Low (<45)**: `#eab308` (yellow-500)
- **Silent-flooded**: `#a855f7` (purple-500)

### Map Legend Icons
- **Circle**: settlements (circle-radius scales with score)
- **Square**: flood extent (semi-transparent blue)
- **Dashed ring**: signal-lost animation (deck.gl)

## Animation

### Durations
- **Fast**: 150ms — hover states
- **Normal**: 300ms — color transitions
- **Slow**: 800ms — map flyTo
- **Pulse**: 2s — signal-lost ring (infinite)

### Easing
- Default: `cubic-bezier(0.4, 0, 0.2, 1)` (Tailwind ease-in-out)

## Icons
Using emoji for now:
- 🛰️ — app logo
- ▶ — run analysis
- ↻ — loading spinner
- 📋 — copy to clipboard

## Accessibility

- **Focus rings**: Blue 2px outline on interactive elements
- **Contrast**: All text meets WCAG AA (4.5:1 minimum)
- **Keyboard nav**: Tab order follows visual hierarchy
- **Screen readers**: aria-labels on icon-only buttons

## Responsive Breakpoints
- **sm**: 640px
- **md**: 768px
- **lg**: 1024px (sidebar switches to horizontal on <lg)
- **xl**: 1280px
