/**
 * Auth fixture for tests that require a logged-in user.
 *
 * Login is OIDC via Keycloak redirect. This fixture navigates to a protected
 * route, drives the Keycloak login form, waits for the redirect back, then
 * hands the authenticated page to the test.
 *
 * Credentials are read from environment variables so they are never hardcoded:
 *   E2E_USERNAME  — Keycloak username  (default: 'testuser')
 *   E2E_PASSWORD  — Keycloak password  (required; no default)
 *
 * Usage in a test file:
 *
 *   import { test, expect } from '@playwright/test'
 *   import { loggedInPage } from '../../fixtures/auth.js'
 *
 *   const authTest = test.extend({ loggedInPage })
 *
 *   authTest('protected page loads', async ({ loggedInPage }) => {
 *       await loggedInPage.goto('/doc-mgr')
 *       // ...
 *   })
 */

import { test } from '@playwright/test'

// Export the fixture function directly so callers compose it with test.extend()
// rather than importing a replacement 'test' object from this file.
export const loggedInPage = async ({ page }, use) => {
    const username = process.env.E2E_USERNAME ?? 'testuser'
    const password = process.env.E2E_PASSWORD

    if (!password) {
        throw new Error('E2E_PASSWORD environment variable is required for authenticated tests')
    }

    // Navigate to a protected route to trigger the OIDC redirect
    await page.goto('/doc-mgr')

    // Wait for Keycloak login page (URL contains /realms/)
    await page.waitForURL(/\/realms\//)

    // Fill and submit the Keycloak login form
    await page.getByLabel('Username or email').fill(username)
    await page.getByLabel('Password').fill(password)
    await page.getByRole('button', { name: 'Sign In' }).click()

    // Wait for redirect back to the app
    await page.waitForURL(/\/doc-mgr/)

    await use(page)
}
