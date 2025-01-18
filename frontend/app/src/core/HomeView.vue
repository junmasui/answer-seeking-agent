<template>
  <h2>Home</h2>
  <v-sheet class="pa-2">
    <p class="pa-2">
      This is an all-in-one user interface to demostrate
      and experiment with
      a modern agentic system.
    </p>
    <p class="pa-2">
      The user interface is separated into a page
      per role of      a possible workflow.
      Each role could have a different level of authorization
      due to considerations such as data access and data destruction possibilities,
      local computing resource demands, cloud service usages, etc.
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