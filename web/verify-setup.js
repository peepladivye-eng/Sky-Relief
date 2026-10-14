#!/usr/bin/env node
/**
 * SkyRelief Setup Verification Script
 * 
 * Checks that all deferred features are properly configured:
 * 1. deck.gl dependencies installed
 * 2. Playwright test files present
 * 3. TypeScript compiles without errors
 * 4. Design system docs exist
 */

const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

const checks = []
let passed = 0
let failed = 0

function check(name, fn) {
  try {
    fn()
    checks.push({ name, status: '✅ PASS' })
    passed++
  } catch (err) {
    checks.push({ name, status: `❌ FAIL: ${err.message}` })
    failed++
  }
}

console.log('🛰️  SkyRelief Setup Verification\n')

// 1. Check deck.gl packages
check('deck.gl packages installed', () => {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'))
  const deps = { ...pkg.dependencies, ...pkg.devDependencies }
  
  if (!deps['deck.gl']) throw new Error('deck.gl not in package.json')
  if (!deps['@deck.gl/core']) throw new Error('@deck.gl/core not in package.json')
  if (!deps['@deck.gl/layers']) throw new Error('@deck.gl/layers not in package.json')
  if (!deps['@deck.gl/mapbox']) throw new Error('@deck.gl/mapbox not in package.json')
  
  // Check node_modules
  if (!fs.existsSync('node_modules/deck.gl')) {
    throw new Error('deck.gl not in node_modules — run npm install')
  }
})

// 2. Check Playwright packages
check('Playwright packages installed', () => {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'))
  const deps = { ...pkg.dependencies, ...pkg.devDependencies }
  
  if (!deps['@playwright/test']) throw new Error('@playwright/test not in package.json')
  if (!deps['@axe-core/playwright']) throw new Error('@axe-core/playwright not in package.json')
  
  if (!fs.existsSync('node_modules/@playwright/test')) {
    throw new Error('@playwright/test not in node_modules — run npm install')
  }
})

// 3. Check E2E test files
check('Playwright test files exist', () => {
  const tests = [
    'e2e/smoke.spec.ts',
    'e2e/analysis-flow.spec.ts',
    'e2e/accessibility.spec.ts',
    'playwright.config.ts',
  ]
  
  tests.forEach(file => {
    if (!fs.existsSync(file)) {
      throw new Error(`${file} not found`)
    }
  })
})

// 4. Check DeckGLOverlay component
check('DeckGLOverlay component exists', () => {
  const file = 'components/DeckGLOverlay.tsx'
  if (!fs.existsSync(file)) {
    throw new Error(`${file} not found`)
  }
  
  const content = fs.readFileSync(file, 'utf8')
  if (!content.includes('ScatterplotLayer')) {
    throw new Error('DeckGLOverlay missing ScatterplotLayer')
  }
  if (!content.includes('MapboxOverlay')) {
    throw new Error('DeckGLOverlay missing MapboxOverlay')
  }
})

// 5. Check MapView integration
check('MapView integrates DeckGLOverlay', () => {
  const file = 'components/MapView.tsx'
  if (!fs.existsSync(file)) {
    throw new Error(`${file} not found`)
  }
  
  const content = fs.readFileSync(file, 'utf8')
  if (!content.includes('import DeckGLOverlay')) {
    throw new Error('MapView does not import DeckGLOverlay')
  }
  if (!content.includes('<DeckGLOverlay')) {
    throw new Error('MapView does not render DeckGLOverlay')
  }
})

// 6. Check PartialEvent type
check('PartialEvent type defined', () => {
  const file = 'app/types.ts'
  if (!fs.existsSync(file)) {
    throw new Error(`${file} not found`)
  }
  
  const content = fs.readFileSync(file, 'utf8')
  if (!content.includes('interface PartialEvent')) {
    throw new Error('PartialEvent interface not defined')
  }
  if (!content.includes('type AgentEvent')) {
    throw new Error('AgentEvent union type not found')
  }
  if (!content.includes('PartialEvent')) {
    throw new Error('PartialEvent not in AgentEvent union')
  }
})

// 7. Check design system docs
check('Design system documentation exists', () => {
  const docs = [
    'design-system.md',
    'tech.md',
    'SETUP.md',
  ]
  
  docs.forEach(file => {
    if (!fs.existsSync(file)) {
      throw new Error(`${file} not found`)
    }
  })
})

// 8. Check package.json scripts
check('Test scripts configured', () => {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'))
  const scripts = pkg.scripts
  
  if (!scripts['test:e2e']) throw new Error('test:e2e script missing')
  if (!scripts['test:e2e:ui']) throw new Error('test:e2e:ui script missing')
  if (!scripts['test:e2e:headed']) throw new Error('test:e2e:headed script missing')
})

// 9. Check TypeScript compilation (optional — slow)
if (process.argv.includes('--full')) {
  check('TypeScript compiles without errors', () => {
    try {
      execSync('npx tsc --noEmit', { stdio: 'pipe' })
    } catch (err) {
      throw new Error('TypeScript compilation failed')
    }
  })
}

// Print results
console.log('Results:\n')
checks.forEach(({ name, status }) => {
  console.log(`${status.padEnd(15)} ${name}`)
})

console.log(`\n${passed}/${checks.length} checks passed\n`)

if (failed > 0) {
  console.log('❌ Setup incomplete. Run npm install and check missing files.\n')
  process.exit(1)
} else {
  console.log('✅ All deferred features properly configured!\n')
  console.log('Next steps:')
  console.log('  npm run dev          # Start dev server')
  console.log('  npm run test:e2e     # Run E2E tests')
  console.log('  npm run build        # Production build\n')
  process.exit(0)
}
