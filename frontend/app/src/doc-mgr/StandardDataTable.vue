<template>
    <div>
        <v-banner v-if="tableOutdated" class="pa-2 ma-2" icon="mdi-alert-circle" color="warning" lines="one">
            <v-banner-text> Newer table data is available. </v-banner-text>
            <template #actions>
                <v-btn variant="text" @click="handleRefresh">Refresh</v-btn>
            </template>
        </v-banner>
        <v-data-table-server v-model="internalSelectedItems" v-model:sort-by="sortBy" v-model:page="page"
            v-model:items-per-page="itemsPerPage" show-select return-object multi-sort
            :items-per-page-options="itemsPerPageOptions" :items-length="totalItems" :headers="headers" :items="items"
            density="compact" item-key="name" @update:options="callLoadItems">
            <!-- Dynamically forward all slots passed to this component.
             * `v-for` iterates over all slots passed.
             * `#[name]=...` creates a template for each slot name with all recieved slotProps
             * `<slot ... /> forwards the recieved slot to the VDataTableServer.
        -->
            <!-- <template v-for="(_, name) in $slots" #[name]="slotProps">
        <slot :name="name" v-bind="slotProps" />
      </template> -->

            <!-- Templates for all column headers.
            Important keys for each header object:
            * text: display name of the column header
            * value: unique key for the column
            * sortable: true if the columnn is sortable
            * align: alignment of the column ("start", "center", "end")
            * width: width of column
            Custom keys (ex: filterable) can be added to the header object.
            -->


            <!-- <template v-for="(header) in props.headers"
                #[`header.${header.value}`]="{ header, sortBy }"> -->
                <!-- Custom header for {{ header.text }} ({{ header.value }}) -->

            <!--  -->

            <template v-for="header in headers"
                #[`header.${header.value}`]="{ column, isSorted, sortBy }">
                <!-- Custom header for {{ header.text }} ({{ header.value }}) -->
                <div style="display: flex; align-items: center;"
                    :width="column.width"
                    :aria-sort="sortDirection(header.value, sortBy)" tabindex="0">
                    <!-- Display text -->
                    <span>{{ header.title }}</span>

                    <!-- up/down badge for sorting -->
                    <v-icon v-if="header.sortable" class="ms-1">
                        {{ sortIcon(header.value, sortBy) }}
                    </v-icon>

                    <!-- number badge for sorting precedence -->
                    <span v-if="header.sortable && sortNumber(header.value, sortBy)"
                        class="v-badge ms-1" style="font-size: 0.75em; color: #1976d2;">
                        {{ sortNumber(header.value, sortBy) }}
                    </span>
                    <!-- filter badge -->
                    <v-menu v-if="header.filterable" v-model="activeFilterEdit[header.value]" :close-on-content-click="false">
                        <template #activator="{ props }">
                            <v-icon v-bind="props" small class="ms-1" color="primary">mdi-filter-variant</v-icon>
                        </template>
                        <v-card>
                            <!-- The clear button does not always emit an input event -->
                            <v-text-field v-model="header.filterModel" :label="`Filter by ${header.title}`"
                                @input="header.onFilterChange" @click:clear="header.onFilterChange"
                                @keydown.enter="setShowFilter(header, false)"
                                clearable dense
                                hide-details />
                            <!-- TODO: There are problems:
                                        @input and @click:clear call out to the parent.
                                        @kyedown.enter only changes the show/hide state.
                                        We need:
                                        when hiding, to call loadItems.
                            -->
                        </v-card>
                    </v-menu>

                </div>
            </template>

            <!-- Customize the contents of the "actions" column for every row. -->
            <template #item.actions="{ item, index }">
                <div class="action-icons">
                    <v-icon class="me-2" size="small" @click="openEditDialog(item, index)">mdi-pencil</v-icon>
                    <v-icon size="small" @click="openDeleteDialog(item, index)">mdi-delete</v-icon>
                </div>
            </template>
        </v-data-table-server>
        <confirmation-dialog v-model:active="activeConfirmEdit" @done="closeEditDialog" @confirmed="confirmEdit">
            <slot name="edit-dialog-text">Are you sure you want to edit this item?</slot>
        </confirmation-dialog>
        <confirmation-dialog v-model:active="activeConfirmDelete" @done="closeDeleteDialog" @confirmed="confirmDelete">
            <slot name="delete-dialog-text">Are you sure you want to delete this item?</slot>
        </confirmation-dialog>
    </div>
</template>

<script setup>
import { ref, watch, defineEmits, defineProps, defineModel, onMounted, onBeforeUnmount, nextTick } from 'vue'
import ConfirmationDialog from '../common/ConfirmationDialog.vue'
import logger from '@/common/Logger'

// Use defineModel for v-model bindings
const selectedItems = defineModel('selectedItems', { type: Array })
const sortBy = defineModel('sortBy', { type: Array })
const page = defineModel('page', { type: Number })
const itemsPerPage = defineModel('itemsPerPage', { type: Number })
const totalItems = defineModel('totalItems', { type: Number })
const items = defineModel('items', { type: Array })
const activeFilterEdit = defineModel('activeFilterEdit', { type: Object })
const shouldReload = defineModel('shouldReload', { type: Boolean })

const props = defineProps({
    headers: Array,
    itemsPerPageOptions: Array,
    editDocument: Function,
    deleteDocument: Function,
    loadItems: Function,
    loadTableStats: Function
})

const emit = defineEmits([
    'edit',
    'delete',
    'refresh',
    'confirmEdit',
    'confirmDelete'
])

const internalSelectedItems = selectedItems
const activeConfirmEdit = ref(false)
const activeConfirmDelete = ref(false)
const targetItem = ref({})
const targetIndex = ref(-1)

function setShowFilter(header, val) {
  activeFilterEdit.value[header.value] = val
}



/**
 * 
 */
function isColumnSorted(columnKey, sortBy) {
    if (Array.isArray(sortBy)) {
        return sortBy.some(s => s.key === columnKey);
    } else if (sortBy && sortBy.key) {
        return sortBy.key === columnKey;
    }
    return false;
}

/**
 * 
 */
function sortDirection(columnKey, sortBy) {
    if (Array.isArray(sortBy)) {
        const matched = sortBy.find(s => s.key === columnKey)
        if (matched) {
            return (matched?.order === 'desc') ? 'descending' : 'ascending'
        }
    } else if (sortBy && sortBy.key) {
        if (sortBy?.key === columnKey) {
            return (sortBy?.order === 'desc') ? 'descending' : 'ascending'
        }
    }
    return 'none'
}

/**
 * 
 */
function sortIcon(columnKey, sortBy) {
    const direction = sortDirection(columnKey, sortBy)
    if (direction === 'descending') { return 'mdi-arrow-down' }
    else if (direction === 'ascending') { return 'mdi-arrow-up' }
    return 'mdi-arrow-up-down'
}

/**
 * 
 */
function sortNumber(columnKey, sortBy) {
    if (Array.isArray(sortBy)) {
        const matchedIndex = sortBy.findIndex(s => s.key === columnKey)
        if (matchedIndex >= 0) {
            return matchedIndex + 1
        }
    } else if (sortBy && sortBy.key) {
        if (sortBy?.key === columnKey) {
            return 1
        }
    }
    return null
}

// Internal state for table freshness
const tableOutdated = ref(false)
const tableUpdatedAt = ref()


/**
 * Watches the `shouldReload` model property for changes.
 * When `shouldReload` is set to `true`, this watcher triggers a refresh of the table data
 * by calling `callLoadItems`. After the data is loaded, it resets `shouldReload` to `false`.
 * This allows parent components to programmatically trigger a data reload.
 * @param {boolean} newVal The new value of `shouldReload`.
 * @param {boolean} _oldVal The old value of `shouldReload`.
 */
watch(shouldReload, async (newVal, _oldVal) => {
    if (newVal) {
        await nextTick()

        await callLoadItems()    

        shouldReload.value = false
    }
})

/**
 * Emits the refresh event to trigger a refresh from the parent.
 */
function handleRefresh() {
    emit('refresh')
}
/**
 * Opens the edit confirmation dialog for a specific item.
 * @param {Object} item - The item to edit
 * @param {number} index - The index of the item in the table
 */
function openEditDialog(item, index) {
    targetItem.value = { ...item }
    targetIndex.value = index
    activeConfirmEdit.value = true
}

/**
 * Closes the edit document dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeEditDialog() {
    await callLoadItems()

    targetItem.value = {}
    targetIndex.value = -1
    activeConfirmEdit.value = false
}
/**
 * Applies the document edit operation after user confirmation.
 * Calls the editDocument function and closes the dialog.
 */
async function applyEditDoc() {
    if (props.editDocument && targetItem.value.id) {
        await props.editDocument(targetItem.value.id)
    }
    await closeEditDialog()
}
/**
 * Opens the delete confirmation dialog for a specific item.
 * @param {Object} item - The item to delete
 * @param {number} index - The index of the item in the table
 */
function openDeleteDialog(item, index) {
    targetItem.value = { ...item }
    targetIndex.value = index
    activeConfirmDelete.value = true
}
/**
 * Closes the delete confirmation dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeDeleteDialog() {
    await callLoadItems()

    targetItem.value = {}
    targetIndex.value = -1
    activeConfirmDelete.value = false
}
/**
 * Applies the deletion operation after user confirmation.
 * Calls the deleteDocument function with the target item's ID.
 */
async function applyDeleteItem() {
    if (props.deleteDocument && targetItem.value.id) {
        await props.deleteDocument(targetItem.value.id)
    }
    await closeDeleteDialog()
}
/**
 * Handles confirmation of edit dialog by applying the edit operation.
 */
function confirmEdit() {
    applyEditDoc()
}
/**
 * Handles confirmation of delete dialog by applying the delete operation.
 */
function confirmDelete() {
    applyDeleteItem()
}

/**
 * Emits the loadTableStats event to request table stats refresh from the parent.
 */
async function callLoadTableStats() {
    try {
        const data = await props.loadTableStats()

        totalItems.value = data.totalItems

        if (tableUpdatedAt.value !== data.tableUpdatedTime) {
            // Since the client-side and the server-side disagree on
            // the last timesteamp that the server-side data was last updated,
            // we set the "outdated" flag.
            tableOutdated.value = true
            tableUpdatedAt.value = data.tableUpdatedTime
        } else {
            // Since the client-side and the server-side agree on
            // the last timesteamp that the server-side data was last updated,
            // we ensure that the "outdated" flag is clear.
            tableOutdated.value = false
        }
    } catch (error) {
        console.error('Error getting table stats:', error)
    }
}

/**
 * Emits the loadItems event to request table data refresh from the parent.
 */
async function callLoadItems() {
    try {
        const data = await props.loadItems()

        totalItems.value = data.totalItems
        items.value = data.items

        // Set the timestamp when the server-side data was last updated.
        tableUpdatedAt.value = data.tableUpdatedTime

        // Since we are loading the client-side data (thru the loadItems call),
        // we clear the "outdated" flag
        tableOutdated.value = false
    } catch (error) {
        console.error('Error getting table items:', error)
    }
}

//
// Polling for server table updates.
//

let intervalId = null

onMounted(async () => {
    await callLoadItems()
    intervalId = setInterval(async () => {
        callLoadTableStats()
    }, 30000)
})

onBeforeUnmount(() => {
    clearInterval(intervalId)
    intervalId = null
})
</script>

<style scoped>
.action-icons {
    display: flex;
    gap: 4px;
    white-space: nowrap;
}
</style>
