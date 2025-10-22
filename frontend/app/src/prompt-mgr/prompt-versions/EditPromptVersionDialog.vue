<template>
  <v-dialog v-model="active" max-width="600px">
    <v-card>
      <v-card-title class="text-h5"> Edit Prompt </v-card-title>
      <v-card-text>
        <v-text-field v-model="modelValue.name" label="Name" variant="outlined" disabled></v-text-field>
        <v-select
          v-model="modelValue.status"
          :items="statusOptions"
          label="Status"
          variant="outlined"
        ></v-select>
        <v-checkbox v-model="modelValue.includeHistory" label="Include History"></v-checkbox>
        <multi-line-text-edit
          v-model="modelValue.systemMessage"
          label="System Message"
        ></multi-line-text-edit>
        <multi-line-text-edit
          v-model="modelValue.humanMessage"
          label="Human Message"
        ></multi-line-text-edit>
        <v-select
          v-model="modelValue.ownerType"
          :items="ownerTypeOptions"
          label="Owner Type"
          variant="outlined"
          disabled
        ></v-select>
        <v-text-field
          v-model="modelValue.version"
          label="Version"
          variant="outlined"
          disabled
        ></v-text-field>
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
import MultiLineTextEdit from '../../common/MultiLineTextEdit.vue'

const active = defineModel('active', {
  type: Boolean,
  default: false
})

const modelValue = defineModel({
  type: Object,
  default: () => {
    return {
      name: '',
      status: 'active',
      includeHistory: true,
      systemMessage: '',
      humanMessage: '',
      ownerType: 'user',
      version: 1
    }
  }
})

const statusOptions = ['active', 'deactivated']
const ownerTypeOptions = ['system', 'user']

const emit = defineEmits(['canceled', 'confirmed', 'done'])

/**
 * Handles the cancel action by emitting appropriate events and closing the dialog.
 * Notifies parent components that the operation was canceled.
 */
function onCancel() {
  emit('canceled')
  emit('done')
  active.value = false
}

/**
 * Handles the confirm action by emitting appropriate events and closing the dialog.
 * Notifies parent components that the operation was confirmed.
 */
function onConfirm() {
  emit('confirmed')
  emit('done')
  active.value = false
}
</script>
