/**
 * Workflow: Prompt Management
 *
 * Verifies that a user can create a prompt, add a version to it,
 * and that the version is selectable in the conversational view.
 * Exercises the prompt API, versioning logic, and UI together.
 */
import { test, expect } from '@playwright/test'

test.skip('prompt can be created, versioned, and used in a query', async () => {})

// Suggested steps when implementing:
//   1. Go to /prompt-mgr, create a new prompt
//   2. Assert it appears in the prompts table
//   3. Navigate to prompt-versions tab, create a version for that prompt
//   4. Assert the version is listed
//   5. Go to /conversational, verify the prompt is selectable
