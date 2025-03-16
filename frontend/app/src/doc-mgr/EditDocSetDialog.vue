<template>
    <v-dialog v-model="active" max-width="600px">
        <v-card>
            <v-card-title class="text-h5">
                Edit Document Set
            </v-card-title>
            <v-card-text>
                <v-text-field clearable label="Name" variant="outlined" v-model="modelValue.name" readOnly></v-text-field>
                <v-checkbox label="Is Public" v-model="modelValue.isPublicViewable"></v-checkbox>
                <v-checkbox label="Is Default" v-model="modelValue.isNewDocDefault"></v-checkbox>
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
});

const modelValue = defineModel({
  type: Object,
  validator: (value) => {
    const requiredKeys = ['key1', 'key2'];
    return requiredKeys.every(key => key in value);
  }
});

const emit = defineEmits(['canceled', 'confirmed', 'done'])

async function onCancel() {
    emit('canceled')
    emit('done')
    active.value = false
}

async function onConfirm() {
    emit('confirmed')
    emit('done')
    active.value = false
}

</script>
<style></style>
