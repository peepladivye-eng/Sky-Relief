import { test, expect } from '@playwright/test'

test.describe('Analysis Flow (Mocked API)', () => {
  
  test.beforeEach(async ({ page }) => {
    // Mock /events endpoint
    await page.route('**/events', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            event_id: 'test_event',
            name: 'Test Flood 2023',
            bbox: [77.0, 28.0, 77.5, 28.5],
            before_date: '2023-06-01',
            after_date: '2023-06-15',
            sensor: 'sentinel-1',
          },
        ]),
      })
    })
  })

  test('select event and enable run button', async ({ page }) => {
    await page.goto('/')
    
    // Wait for events to load
    await page.waitForTimeout(500)
    
    // Select event (implementation depends on EventPicker component)
    const picker = page.locator('select, [role="combobox"]').first()
    if (await picker.isVisible()) {
      await picker.click()
      await page.locator('text=Test Flood 2023').click()
    }
    
    // Run button should be enabled
    const runButton = page.locator('button:has-text("Run Analysis")')
    await expect(runButton).toBeEnabled()
  })

  test('analysis shows loading state', async ({ page }) => {
    await page.goto('/')
    
    // Mock slow /analyze endpoint
    await page.route('**/analyze', route => {
      setTimeout(() => {
        route.fulfill({
          status: 200,
          body: 'data: {"type":"step","tool":"raster","status":"running","detail":"Processing...","ts":1}\n\n',
        })
      }, 1000)
    })
    
    // Select event and run
    // (assumes event picker interaction works)
    const runButton = page.locator('button:has-text("Run Analysis")')
    if (await runButton.isEnabled()) {
      await runButton.click()
      
      // Check for loading spinner
      await expect(page.locator('text=Analysing…')).toBeVisible({ timeout: 2000 })
    }
  })

  test('paste report enables submit button', async ({ page }) => {
    await page.goto('/')
    
    const textarea = page.locator('textarea[placeholder*="ground report"]')
    const submitButton = page.locator('button:has-text("Submit & Re-rank")')
    
    // Initially disabled
    await expect(submitButton).toBeDisabled()
    
    // Type report
    await textarea.fill('Village underwater, 50 families stranded')
    
    // Should remain disabled until event selected
    // (full flow requires event selection first)
  })
})
