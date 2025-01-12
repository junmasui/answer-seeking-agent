<template>
    <v-dialog v-model="active" max-width="500px">
        <v-card>
            <v-card-title class="text-h5">
                <slot></slot>
            </v-card-title>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue-darken-1" variant="text" @click="onCancel">Cancel</v-btn>
                <v-btn color="blue-darken-1" variant="text" @click="onConfirm">OK</v-btn>
                <v-spacer></v-spacer>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup>
import { defineModel } from 'vue';

const active = defineModel('active', {
    type: Boolean,
    default: false
});

const emit = defineEmits(['canceled', 'confirmed'])

async function onCancel() {
    emit('canceled')
    active.value = false
}

async function onConfirm() {
    emit('confirmed')
    active.value = false
}

</script>
<style></style>