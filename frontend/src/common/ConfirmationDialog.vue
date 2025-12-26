<template>
  <v-dialog v-model="active" max-width="600px">
    <v-card>
      <v-card-title class="text-h5">
        <slot></slot>
      </v-card-title>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="text" @click="onCancel">Cancel</v-btn>
        <v-btn color="primary" variant="text" @click="onConfirm">OK</v-btn>
        <v-spacer></v-spacer>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
const active = defineModel('active', {
  type: Boolean,
  default: false
})

const emit = defineEmits(['canceled', 'confirmed', 'done'])

/**
 * Handles the cancel action by emitting appropriate events and closing the dialog.
 * Notifies parent components that the user chose to cancel the operation.
 */
function onCancel() {
  emit('canceled')
  emit('done')
  active.value = false
}

/**
 * Handles the confirm action by emitting appropriate events and closing the dialog.
 * Notifies parent components that the user confirmed the operation should proceed.
 */
function onConfirm() {
  emit('confirmed')
  emit('done')
  active.value = false
}
</script>
