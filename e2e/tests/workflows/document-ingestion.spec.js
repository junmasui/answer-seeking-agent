/**
 * Workflow: Document Ingestion
 *
 * Verifies the full pipeline from upload → ingest → document appears
 * as ingested in the doc manager. Each step's effect must be visible
 * in the UI before proceeding to the next.
 */
import { test, expect } from '@playwright/test'

test.skip('document flows from upload through ingest to queryable', async () => {})

// Suggested steps when implementing:
//   1. Go to /doc-mgr (doc sets tab), create or select a doc set
//   2. Go to /doc-mgr/upload-files, upload a fixture file
//   3. Assert upload confirmation appears
//   4. Go to /doc-mgr/docs, find the uploaded document
//   5. Trigger ingest, poll/wait for status to become "Ingested"
//   6. Assert the document is listed with ingested status
