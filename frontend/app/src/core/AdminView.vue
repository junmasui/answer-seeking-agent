<template>
    <h2>Health Check</h2>
    <v-container class="ma-0 pa-0">
        <v-sheet class="ma-2 pa-2">
            Reset tracking table, vector store, and file store.
            <v-btn class="ma-2" size="large" @click="onResetDatabase">Reset</v-btn>
        </v-sheet>
        <v-sheet class="ma-2 pa-2">
            Placeholder for next administrative task
        </v-sheet>
    </v-container>

    <confirmation-dialog v-model:active="confirmReset" @confirmed="resetConfirmed">
        Are you sure you want to reset all data?
    </confirmation-dialog>

</template>

<script setup>
import { ref, onMounted } from 'vue';
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import ConfirmationDialog from '../common/ConfirmationDialog.vue';

const currentUserStore = useCurrentUserStore();

const { signedIn, accessToken } = storeToRefs(currentUserStore)

const confirmReset = ref(false)

function onResetDatabase() {
    confirmReset.value = true
}

async function resetConfirmed() {
    try {

        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }
        const response = await fetch('/api/admin/resetDatabase', {
            method: 'POST',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Database reset failed');
        }

        const data = await response.json();
        console.log(`Database reset succeeded`, data);
    } catch (error) {
        console.error('Error reseting database:', error);
    }

}

</script>

<style></style>