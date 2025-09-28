<template>
  <h2>Agent Diagram</h2>
  <v-container>
    <v-col cols="auto">
      <v-card variant="elevated" class="mx-auto pa-4 ma-2 diagram-card">
        <component
          :is="MermaidDiagramComponent"
          class="diagram-renderer"
          :definition="mermaidDiagram"
        >
          <template #placeholder>
            <div class="diagram-placeholder">
              <v-progress-circular
                v-if="isLoading"
                indeterminate
                color="primary"
                size="32"
                class="mr-3"
              />
              <span>
                {{ isLoading ? 'Loading diagram…' : 'Diagram not available.' }}
              </span>
            </div>
          </template>
          <template #error="{ message }">
            <div class="diagram-error">Failed to render diagram: {{ message }}</div>
          </template>
        </component>

        <v-alert v-if="fetchError" type="error" variant="tonal" class="mt-4" density="comfortable">
          {{ fetchError }}
        </v-alert>
      </v-card>
    </v-col>

    <v-col cols="auto">
      <v-btn
        class="ma-2"
        size="large"
        color="primary"
        variant="elevated"
        :loading="isLoading"
        @click="getDiagram"
      >
        Refresh
      </v-btn>
      <v-btn
        class="ma-2"
        size="large"
        color="secondary"
        variant="elevated"
        :disabled="!mermaidDiagram"
        @click="copyDiagram"
      >
        Copy to Clipboard
      </v-btn>
      <v-btn
        class="ma-2"
        size="large"
        color="secondary"
        variant="outlined"
        :disabled="!mermaidDiagram"
        @click="saveDiagram"
      >
        Download diagram
      </v-btn>
    </v-col>
  </v-container>
</template>

<script setup>
import { ref, watch, defineAsyncComponent } from 'vue'
import { storeToRefs } from 'pinia'
import logger from '../common/Logger.js'
import { getAuthorization } from '../common/AuthUtils.js'

import { useCurrentUserStore } from '../common/CurrentUserStore'

const mermaidDiagram = ref('')
const isLoading = ref(false)
const fetchError = ref('')
const signInMessage = 'Sign in to view the diagram.'
const MermaidDiagramComponent = defineAsyncComponent(() => import('../common/MermaidDiagram.vue'))

const currentUserStore = useCurrentUserStore()
const { signedIn, accessToken } = storeToRefs(currentUserStore)

/**
 * Handles the manual status check button click.
 * Resets the status to unknown and triggers a fresh status check from the server.
 */
async function getDiagram() {
  if (!signedIn.value) {
    fetchError.value = signInMessage
    mermaidDiagram.value = ''
    return
  }

  await downloadMermaidDiagram()
}

async function copyDiagram() {
  if (!mermaidDiagram.value) {
    fetchError.value = 'Diagram not available to copy.'
    return
  }

  fetchError.value = ''

  if (typeof navigator === 'undefined' || !navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') {
    fetchError.value = 'Clipboard access is not available in this browser.'
    return
  }

  try {
    await navigator.clipboard.writeText(mermaidDiagram.value)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown clipboard error'
    fetchError.value = `Failed to copy diagram: ${message}`
    logger.apiError('Copy diagram failed', error)
  }
}

function saveDiagram() {
  if (!mermaidDiagram.value) {
    fetchError.value = 'Diagram not available to save.'
    return
  }

  fetchError.value = ''

  try {
    if (typeof document === 'undefined' || !document.body || typeof URL === 'undefined' || typeof URL.createObjectURL !== 'function') {
      fetchError.value = 'Saving files is not supported in this environment.'
      return
    }

    const blob = new Blob([mermaidDiagram.value], {
      type: 'text/plain;charset=utf-8'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'agent-diagram.mmd'
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown file save error'
    fetchError.value = `Failed to save diagram: ${message}`
    logger.apiError('Save diagram failed', error)
  }
}

/**
 * Performs a health check by calling the server status endpoint.
 * Updates the system status display and handles offline scenarios with proper error logging.
 */
async function downloadMermaidDiagram() {
  if (!signedIn.value) {
    fetchError.value = signInMessage
    mermaidDiagram.value = ''
    isLoading.value = false
    return
  }

  isLoading.value = true
  fetchError.value = ''
  try {
    const headers = {
      Accept: 'application/vnd.mermaid',
      'Content-Type': 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const response = await fetch('/api/answer/mermaid', {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      throw new Error(`Diagram request failed (${response.status} ${response.statusText})`)
    }

    const content = await response.text()

    mermaidDiagram.value = content || ''
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'
    fetchError.value = message
    logger.apiError('Diagram request failed', error)
  } finally {
    isLoading.value = false
  }
}

watch(
  [signedIn, accessToken],
  async ([newSignedIn, newAccessToken]) => {
    if (!newSignedIn || !newAccessToken) {
      fetchError.value = signInMessage
      mermaidDiagram.value = ''
      isLoading.value = false
      return
    }

    await downloadMermaidDiagram()
  },
  { immediate: true }
)
</script>

<style>
nav,
main {
  border: 2px solid #000;
  margin-bottom: 10px;
  padding: 10px;
}

nav > a + a {
  margin-left: 10px;
}

h2 {
  border-bottom: 1px solid #ccc;
  margin: 0 0 20px;
}

.diagram-card {
  max-width: 720px;
  width: 100%;
}

.diagram-renderer {
  min-height: 220px;
}

.diagram-placeholder {
  align-items: center;
  color: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  min-height: 220px;
  text-align: center;
}

.diagram-error {
  background-color: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.4);
  border-radius: 8px;
  color: #ff7961;
  margin-top: 16px;
  padding: 16px;
}
</style>
