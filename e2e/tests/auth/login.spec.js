import { test, expect } from '@playwright/test'

test('unauthenticated access to protected route redirects to login', async ({ page }) => {
    const response = await page.goto('/doc-mgr')
    // Router guard redirects to /login before any network request fails
    await expect(page).toHaveURL(/\/login/)
})
