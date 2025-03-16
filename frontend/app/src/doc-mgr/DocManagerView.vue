<template>
    <h2>Document Manager</h2>

    <v-tabs v-model="activeTabModel" bg-color="primary">
        <v-tab value="docSets" :to="{ name: 'doc-sets' }">Document Sets</v-tab>
        <v-tab value="upload" :to="{ name: 'upload-files' }">Upload Files</v-tab>
        <v-tab value="docs" :to="{ name: 'docs' }">Documents</v-tab>
    </v-tabs>

    <router-view></router-view>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const activeTabModel = ref()

</script>

<style>
h2 {
    border-bottom: 1px solid #ccc;
    margin: 0 0 20px;
}
</style>