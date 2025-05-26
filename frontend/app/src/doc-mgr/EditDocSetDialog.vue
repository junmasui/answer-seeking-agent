<template>
  <v-dialog v-model="active" max-width="600px">
    <v-card>
      <v-card-title class="text-h5"> Edit Document Set </v-card-title>
      <v-card-text>
        <v-text-field
          v-model="modelValue.name"
          clearable
          label="Name"
          variant="outlined"
          read-only
        ></v-text-field>
        <v-checkbox v-model="modelValue.isPublicViewable" label="Is Public"></v-checkbox>
        <v-checkbox v-model="modelValue.isNewDocDefault" label="Is Default"></v-checkbox>
      </v-card-text>
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

const modelValue = defineModel({
  type: Object,
  validator: (value) => {
    const requiredKeys = ['key1', 'key2']
    return requiredKeys.every((key) => key in value)
  }
})

const emit = defineEmits(['canceled', 'confirmed', 'done'])

/**
 * Handles the cancel action by emitting appropriate events and closing the dialog.
 * Notifies parent components that the operation was canceled.
 */
async function onCancel() {
  emit('canceled')
  emit('done')
  active.value = false
}

/**
 * Handles the confirm action by emitting appropriate events and closing the dialog.
 * Notifies parent components that the operation was confirmed.
 */
async function onConfirm() {
  emit('confirmed')
  emit('done')
  active.value = false
}
</script>
