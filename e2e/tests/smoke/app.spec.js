import { test, expect } from '@playwright/test'

test('homepage responds without server error', async ({ page }) => {
    const response = await page.goto('/')
    expect(response.status()).toBeLessThan(500)
})
