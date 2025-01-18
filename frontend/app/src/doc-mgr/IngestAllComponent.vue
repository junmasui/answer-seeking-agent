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

const currentUserStore = useCurrentUserStore();

const { signedIn, accessToken } = storeToRefs(currentUserStore)

async function onIngest(event) {
    try {
        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const response = await fetch('/api/ingest', {
            method: 'POST',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Ingest failed');
        }

        const data = await response.json();
        console.log('Ingest started successfully:', data);
    } catch (error) {
        console.error('Error ingesting:', error);
    }
}

</script>

<style module>
</style>