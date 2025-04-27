<template>
    <v-container>
        <v-btn class="ma-2" size="large" :disabled="disableUpload" @click="onUpload">Upload Files</v-btn>
        <v-autocomplete
            class="ma-2"
            variant="outlined"
            label="Document Set"
            v-model="selectedDocSet"
            :items="documentSets"
            item-title="name"
            item-id="id"
            return-object
        ></v-autocomplete>

        <v-container>
            <v-row class="flex-nowrap" no-gutters>
                <v-col cols="4"> </v-col>
                <v-col cols="4" class="justify-center max-width: 200px">
                    <v-progress-linear :active="downloading" :indeterminate="true"
                        color="primary"></v-progress-linear>
                </v-col>
                <v-col cols="4"> </v-col>
            </v-row>
        </v-container>

        <v-file-upload class="ma-2" clearable density="default" v-model="fileList"
            v-bind:multiple="true"></v-file-upload>

    </v-container>

</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, toRaw } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import { useUploadStore } from './UploadStore';

const currentUserStore = useCurrentUserStore();
const updateStore = useUploadStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)
const { fileList, selectedDocSet } = storeToRefs(updateStore);

const downloading = ref(false)

const disableUpload = computed(() => {
    // The upload button is enabled only when all these conditions are met:
    // 1. Document set is selected.
    // 2. One or more files are selected.
    // 3. Currently not uploading.
    const enabled = selectedDocSet.value !== null && fileList.value.length > 0 && ! downloading.value;

    return ! enabled;
})

const documentSets = ref([])
const documentSetCount = ref(0);
const documentSetsUpdatedAt = ref();
const documentSetsOutdated = ref(false);

async function onUpload() {
    downloading.value = true;

    try {
        while (fileList.value.length > 0) {
            const file = fileList.value.pop()
            // Upload the file
            console.log(`Uploading file: ${file.name}`)

            const CHUNK_SIZE = 0.5 * 1024 * 1024; // 05.MB chunks
            const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

            try {
                for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
                    const start = chunkIndex * CHUNK_SIZE;
                    const end = start + CHUNK_SIZE;
                    const chunk = file.slice(start, end);

                    const formData = new FormData();
                    const isoString = new Date().toISOString().split('.')[0] + 'Z';
                    var contentType = 'application/pdf';
                    formData.append('file', chunk, file.name);
                    formData.append('sourceUrl', 'https://localhost/files/'+file.name);
                    formData.append('contentType', contentType);
                    formData.append('downloadTimeUtc', isoString);
                    formData.append('chunkIndex', chunkIndex);
                    formData.append('totalChunks', totalChunks);
                    formData.append('documentSetId', selectedDocSet.value.id)

                    const headers = {
                        'Accept': 'application/json'
                    }
                    if (signedIn.value) {
                        headers['Authorization'] = `Bearer ${accessToken.value}`
                    }
                    const response = await fetch('/api/documents/upload', {
                        method: 'POST',
                        body: formData,
                        headers: headers
                    });

                    if (!response.ok) {
                        throw new Error('File upload failed');
                    }

                    const data = await response.json();
                    console.log(`File uploaded successfully: ${chunkIndex} ${totalChunks}`, data);

                }

            } catch (error) {
                console.error('Error uploading file:', error);
            }

            console.log(`Uploaded file: ${file.name}`)
        }

    } finally {
        downloading.value = false;
    }
}


//
// Polling for server table updates.
//

var intervalId = null;

onMounted(async () => {
    await loadDocumentSets();

    intervalId = setInterval(async () => {
        await loadTableStats()
    },
        30000)
})

onBeforeUnmount(async () => {
    clearInterval(intervalId);
    intervalId = null;
})

async function loadTableStats() {
    try {

        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const response = await fetch(`/api/document-sets/stats`, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Getting table stats failed');
        }

        const data = await response.json();

        documentSetCount.value = data.documentSetCount;
        if (documentSetsUpdatedAt.value !== data.tableUpdatedTime) {
            documentSetsOutdated.value = true;
            documentSetsUpdatedAt.value = data.tableUpdatedTime;
        }
    } catch (error) {
        console.error('Error getting table stats:', error);
    }
}

async function loadDocumentSets() {
    try {
        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const params = new URLSearchParams({
        })

        const response = await fetch(`/api/document-sets/?${params}`, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Failed to get document sets');
        }

        const data = await response.json();

        documentSets.value = data.documentSets.map(item => toRaw(item));

    } catch (error) {
        documentSets.value = [];
        console.error('Error getting document sets:', error);
    }
}

</script>

<style module></style>