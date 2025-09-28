<template>
  <div class="mermaid-wrapper">
    <div v-if="!hasContent && !errorMessage" class="mermaid-placeholder">
      <slot name="placeholder">No diagram available.</slot>
    </div>
    <div v-else-if="errorMessage" class="mermaid-error">
      <slot name="error" :message="errorMessage">{{ errorMessage }}</slot>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-else class="mermaid-diagram" v-html="svg" />
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import mermaid from 'mermaid'

const props = defineProps({
  definition: {
    type: String,
    default: ''
  },
  theme: {
    type: String,
    default: 'neutral'
  },
  securityLevel: {
    type: String,
    default: 'loose'
  }
})

const svg = ref('')
const errorMessage = ref('')

const hasContent = computed(() => Boolean(props.definition?.trim()))

const renderDiagram = async () => {
  if (!hasContent.value) {
    svg.value = ''
    errorMessage.value = ''
    return
  }

  try {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: props.securityLevel,
      theme: props.theme
    })

    const renderKey = `mermaid-diagram-${Math.random().toString(36).slice(2)}`
    const { svg: renderedSvg } = await mermaid.render(renderKey, props.definition)

    svg.value = renderedSvg
    errorMessage.value = ''
  } catch (err) {
    console.error('Mermaid render failed', err)
    errorMessage.value = err instanceof Error ? err.message : 'Failed to render diagram'
    svg.value = ''
  }
}

watch(
  () => [props.definition, props.theme, props.securityLevel],
  () => {
    renderDiagram()
  },
  { immediate: true }
)
</script>

<style scoped>
.mermaid-wrapper {
  min-height: 180px;
  position: relative;
}

.mermaid-diagram :deep(svg) {
  width: 100%;
  height: auto;
}

.mermaid-placeholder,
.mermaid-error {
  align-items: center;
  border: 1px dashed rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  color: rgba(0, 0, 0, 0.6);
  display: flex;
  font-size: 0.95rem;
  justify-content: center;
  min-height: 180px;
  padding: 24px;
  text-align: center;
}

.mermaid-error {
  border-color: rgba(229, 57, 53, 0.4);
  color: #d32f2f;
  background: rgba(229, 57, 53, 0.08);
}
</style>
