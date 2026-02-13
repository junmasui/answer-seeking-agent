# Frontend Agent Operating Guide

## Framework

- **Core**: Vue 3 + Options API/Vite.
- **Styling**: Vuetify.

## Package Management (npm)

- **Install**: `npm install` (Node 20+).
- **Run**: `npm run dev`.
- **Build**: `npm run build`.
- **Lint**: `npm run lint` or `npm run lint:fix`. (ESLint with auto-fix).
- **CI**: `npm run lint:ci` (zero warnings).

## Code Style & Conventions

- **Structure**:

  ```text
  frontend/src/
  ├── components/    # Dumb UI components (buttons, cards)
  ├── composables/   # Shared logic (store, api calls)
  ├── views/         # Route-level pages
  └── App.vue        # Root
  ```

- **Assets**: Keep paths relative to `src` (e.g., `@/assets/logo.png`).
- **Design & Styling**:
  - **Framework**: Vuetify 3.
  - **Rule**: Prefer **Utility Classes** (e.g., `class="d-flex align-center my-4"`) over custom CSS.
  - **Rule**: Use `<style scoped>` only for non-standard tweaks.
  - **Responsiveness**: Use Vuetify grid (`v-row`/`v-col`) or flex utilities.

## Golden Path Implementation

### Vue Component (Script Setup + TypeScript)

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

// Props definition
const props = defineProps<{
  title: string;
  isActive?: boolean;
}>();

// Reactive state
const count = ref(0);

// Computed
const titleClass = computed(() => props.isActive ? 'text-primary' : 'text-grey');

function increment() {
  count.value++;
}
</script>

<template>
  <v-card class="mx-auto my-4" max-width="400" elevation="2">
    <v-card-title :class="titleClass">
      {{ title }}
    </v-card-title>
    
    <v-card-text>
      Count: {{ count }}
    </v-card-text>
    
    <v-card-actions>
      <v-btn color="primary" variant="text" @click="increment">
        Add
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
```

## Testing

- Ensure linting passes before PRs.
