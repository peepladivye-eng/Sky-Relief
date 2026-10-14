import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Accessibility (WCAG AA)', () => {
  
  test('homepage has no critical a11y violations', async ({ page }) => {
    await page.goto('/')
    
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    
    // Filter out known false positives if any
    const violations = results.violations.filter(
      v => !['color-contrast'].includes(v.id)  // Adjust based on design system
    )
    
    expect(violations).toEqual([])
  })

  test('keyboard navigation works for main controls', async ({ page }) => {
    await page.goto('/')
    
    // Tab through interactive elements
    await page.keyboard.press('Tab')  // Language EN button
    await expect(page.locator('button:has-text("EN")')).toBeFocused()
    
    await page.keyboard.press('Tab')  // Language HI button
    await expect(page.locator('button:has-text("हि")')).toBeFocused()
    
    // Continue tabbing to event picker, run button, etc.
    await page.keyboard.press('Tab')
    // (exact flow depends on component structure)
  })

  test('focus indicators are visible', async ({ page }) => {
    await page.goto('/')
    
    const enButton = page.locator('button:has-text("EN")')
    await enButton.focus()
    
    // Check for focus ring (Tailwind default or custom)
    const focused = await enButton.evaluate(el => {
      const styles = window.getComputedStyle(el)
      return {
        outline: styles.outline,
        boxShadow: styles.boxShadow,
      }
    })
    
    // Should have some visible focus indicator
    expect(focused.outline !== 'none' || focused.boxShadow !== 'none').toBeTruthy()
  })

  test('images and icons have proper alt text', async ({ page }) => {
    await page.goto('/')
    
    // Check that any img elements have alt attributes
    const images = await page.locator('img').all()
    for (const img of images) {
      const alt = await img.getAttribute('alt')
      expect(alt).toBeTruthy()  // Should not be null or empty
    }
    
    // Icon-only buttons should have aria-label
    const iconButtons = await page.locator('button:not(:has-text(""))').all()
    for (const btn of iconButtons) {
      const label = await btn.getAttribute('aria-label')
      const text = await btn.textContent()
      expect(label || text?.trim()).toBeTruthy()
    }
  })

  test('color contrast meets WCAG AA', async ({ page }) => {
    await page.goto('/')
    
    // Run axe contrast checks
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .disableRules([
        'region',        // Allow semantic HTML to be flexible
        'landmark-one-main',
      ])
      .analyze()
    
    const contrastViolations = results.violations.filter(v => v.id === 'color-contrast')
    expect(contrastViolations).toEqual([])
  })
})
