<template>
    <v-dialog v-model="active" max-width="600px">
        <v-card>
            <v-card-title class="text-h5">
                <slot></slot>
            </v-card-title>
            <v-card-text class="text-h6">
                <v-autocomplete
                    v-model="selectedItem"
                    :items="items"
                    :item-title="itemTitle"
                    :item-value="itemValue"
                    return-object
                ></v-autocomplete>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" variant="text" @click="onCancel">Cancel</v-btn>
                <v-btn color="primary" variant="text" @click="onSelect">OK</v-btn>
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

const selectedItem = defineModel('selectedItem', {
    type: Object,
    default: null
})

const props = defineProps(
    {
        items: {
            type: Array,
            required: true
        },
        itemTitle: {
            type: String,
            required: true
        },
        itemValue: {
            type: String,
            required: true
        }
    }
)

const emit = defineEmits(['canceled', 'selected'])

async function onCancel() {
    emit('canceled')
    active.value = false
}

async function onSelect() {
    emit('selected')
    active.value = false
}

</script>
<style></style>