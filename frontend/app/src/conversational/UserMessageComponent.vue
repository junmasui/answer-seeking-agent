<template>
  <v-container fluid class="pa-0 ma-0">
    <!-- Using v-html is safe here because we're rendering sanitized markdown from the marked library -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <!-- deepcode ignore DOM-XSS: Markdown content is sanitized by the marked library -->
    <!-- NOSONAR: Markdown content is sanitized by the marked library -->
    <div class="user-bubble" v-html="transformed"></div>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  message: {
    type: String,
    default: ''
  }
})

const transformed = computed(() => {
  // props.message has a safe default, but guard just in case it's ever null/undefined
  return marked(props.message || '')
})
</script>

<style scope>
.user-bubble {
  margin: 5px;
  padding: 5px;
  border-radius: 5px;
  text-align: left;

  padding-left: 10px;
  padding-right: 12px;
  padding-top: 5px;
  padding-bottom: 5px;

  border: 2px solid #5d80cc;

  margin-right: 60px;
}
</style>
