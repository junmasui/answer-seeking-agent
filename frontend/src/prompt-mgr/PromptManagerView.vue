<template>
  <h2>Prompt Manager</h2>

  <v-tabs v-model="activeTabModel" bg-color="primary">
    <v-tab value="prompts" :to="{ name: 'prompts' }">Prompts</v-tab>
    <v-tab value="promptVersions" :to="{ name: 'prompt-versions' }">Versions</v-tab>
  </v-tabs>

  <router-view></router-view>
</template>

<script setup>
import { ref } from 'vue'

const activeTabModel = ref()
</script>

<style>
h2 {
  border-bottom: 1px solid #ccc;
  margin: 0 0 20px;
}
</style>
