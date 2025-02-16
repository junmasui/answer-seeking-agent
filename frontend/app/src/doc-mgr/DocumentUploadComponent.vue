<template>
    <v-container>
        <v-btn class="ma-2" size="large" :disabled="downloading" @click="onUpload">Upload Files</v-btn>

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
import { ref } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import { useUploadStore } from './UploadStore';

const currentUserStore = useCurrentUserStore();
const updateStore = useUploadStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)
const { fileList } = storeToRefs(updateStore);

const downloading = ref(false)

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
                    formData.append('file', chunk, file.name);
                    formData.append('chunkIndex', chunkIndex);
                    formData.append('totalChunks', totalChunks);

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

</script>

<style module></style>