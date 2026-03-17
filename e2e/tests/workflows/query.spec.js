/**
 * Workflow: Conversational Query
 *
 * Verifies that a user can select a doc set, submit a question,
 * and receive an answer — exercising the API server, vector store,
 * and LLM pipeline together.
 *
 * Prerequisite: at least one ingested doc set exists (created by
 * document-ingestion workflow or a fixture doc set seeded in the DB).
 */
import { test, expect } from '@playwright/test'

test.skip('user can submit a question and receive an answer', async () => {})

// Suggested steps when implementing:
//   1. Go to /conversational
//   2. Select a doc set from the picker
//   3. Type a question into the input and submit
//   4. Wait for the agent response to appear (may take several seconds)
//   5. Assert response is non-empty and no error state is shown
