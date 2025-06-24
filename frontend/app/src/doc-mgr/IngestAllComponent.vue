<template>
  <v-container>
    <v-col cols="auto">
      <v-btn class="ma-2" size="large" @click="onIngest">Ingest All</v-btn>
    </v-col>
  </v-container>
</template>

<script setup>
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import logger from '../common/Logger.js'
import { getAuthorization } from '../common/AuthUtils.js'

const currentUserStore = useCurrentUserStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)

/**
 * Handles the ingest all operation by sending a request to process all uploaded documents.
 * Initiates server-side ingestion of all available documents with proper authentication.
 */
async function onIngest() {
  try {
    const headers = {
      Accept: 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const response = await fetch('/api/ingest', {
      method: 'POST',
      headers
    })

    if (!response.ok) {
      throw new Error('Ingest failed')
    }

    await response.json()
    logger.apiSuccess('Ingest all started')
  } catch (error) {
    logger.apiError('Ingest all failed', error)
  }
}
</script>

<!-- CSS modules - enables locally scoped CSS class names to avoid style conflicts -->
<style module></style>
