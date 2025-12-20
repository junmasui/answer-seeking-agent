<template>
  <v-textarea v-model="modelValue" :label="label" variant="outlined" auto-grow rows="3"></v-textarea>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: ''
  }
})

const modelValue = defineModel()
</script>
