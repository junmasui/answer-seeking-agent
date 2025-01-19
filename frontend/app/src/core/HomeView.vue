<template>
  <h2>Home</h2>
  <v-sheet class="pa-2">
    <p class="pa-2">
      This is an all-in-one user interface to demostrate
      and experiment with
      a modern agentic system.
    </p>
    <p class="pa-2">
    Have fun experimenting! 
    </p>
  </v-sheet>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goToAbout() {
  router.push('/about')
}

</script>

<style></style>