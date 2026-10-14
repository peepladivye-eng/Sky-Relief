import { test, expect } from '@playwright/test'

test.describe('SkyRelief Smoke Tests', () => {
  
  test('homepage loads and shows event picker', async ({ page }) => {
    await page.goto('/')
    
    // Check title
    await expect(page.locator('h1')).toHaveText('SkyRelief')
    
    // Check event picker exists
    const picker = page.locator('text=Select Event')
    await expect(picker).toBeVisible()
    
    // Check language switcher
    await expect(page.locator('button:has-text("EN")')).toBeVisible()
    await expect(page.locator('button:has-text("हि")')).toBeVisible()
  })

  test('run analysis button is disabled without event', async ({ page }) => {
    await page.goto('/')
    
    const runButton = page.locator('button:has-text("Run Analysis")')
    await expect(runButton).toBeDisabled()
  })

  test('language switch toggles between EN and HI', async ({ page }) => {
    await page.goto('/')
    
    const enButton = page.locator('button:has-text("EN")')
    const hiButton = page.locator('button:has-text("हि")')
    
    // Default is EN
    await expect(enButton).toHaveClass(/bg-blue-600/)
    
    // Switch to Hindi
    await hiButton.click()
    await expect(hiButton).toHaveClass(/bg-orange-600/)
    
    // Switch back to English
    await enButton.click()
    await expect(enButton).toHaveClass(/bg-blue-600/)
  })

  test('map initializes with empty state', async ({ page }) => {
    await page.goto('/')
    
    // Check map container exists
    const mapContainer = page.locator('div').filter({ hasText: '🛰️' }).nth(1)
    await expect(mapContainer).toBeVisible()
    
    // Check empty state message
    await expect(page.locator('text=Select an event and run analysis')).toBeVisible()
  })

  test('paste report textarea is present', async ({ page }) => {
    await page.goto('/')
    
    const textarea = page.locator('textarea[placeholder*="ground report"]')
    await expect(textarea).toBeVisible()
    
    const submitButton = page.locator('button:has-text("Submit & Re-rank")')
    await expect(submitButton).toBeVisible()
    await expect(submitButton).toBeDisabled()
  })
})
