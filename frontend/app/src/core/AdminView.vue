<template>
  <h2>Health Check</h2>
  <v-container class="ma-0 pa-0">
    <v-sheet class="ma-2 pa-2">
      Reset tracking table, vector store, and file store.
      <v-btn class="ma-2" size="large" @click="onResetDatabase">Reset</v-btn>
    </v-sheet>
    <v-sheet class="ma-2 pa-2"> Placeholder for next administrative task </v-sheet>
  </v-container>

  <confirmation-dialog v-model:active="confirmReset" @confirmed="resetConfirmed">
    Are you sure you want to reset all data?
  </confirmation-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import ConfirmationDialog from '../common/ConfirmationDialog.vue'
import { getAuthorization } from '../common/AuthUtils.js'

const currentUserStore = useCurrentUserStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)

const confirmReset = ref(false)

/**
 * Opens the confirmation dialog for database reset operation.
 * Shows a confirmation prompt before proceeding with the destructive reset action.
 */
function onResetDatabase() {
  confirmReset.value = true
}

/**
 * Executes the database reset operation after user confirmation.
 * Sends a request to reset the tracking table, vector store, and file store.
 */
async function resetConfirmed() {
  try {
    const headers = {
      Accept: 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const response = await fetch('/api/admin/resetDatabase', {
      method: 'POST',
      headers
    })

    if (!response.ok) {
      throw new Error('Database reset failed')
    }

    await response.json()
  } catch (error) {
    console.error('Error reseting database:', error)
  }
}
</script>
