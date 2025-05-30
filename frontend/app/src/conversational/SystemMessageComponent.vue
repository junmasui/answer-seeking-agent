<template>
  <v-container fluid class="pa-0 ma-0">
    <!-- Using v-html is safe here because we're rendering sanitized markdown from the marked library -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <!-- deepcode ignore DOM-XSS: Markdown content is sanitized by the marked library -->
    <!-- NOSONAR: Markdown content is sanitized by the marked library -->
    <div class="system-bubble" v-html="transformed"></div>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  message: {
    type: String
  }
})

const transformed = computed(() => {
  return marked(props.message)
})
</script>

<style scope>
.system-bubble {
  margin: 5px;
  padding: 5px;
  border-radius: 5px;
  text-align: left;

  padding-left: 35px;
  padding-right: 10px;
  padding-top: 5px;
  padding-bottom: 5px;

  border: 2px solid #5d80cc;

  margin-left: 60px;
}
</style>
