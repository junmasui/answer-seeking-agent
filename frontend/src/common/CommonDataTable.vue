<template>
  <div>
    <v-banner
      v-if="tableOutdated"
      class="pa-2 ma-2"
      icon="mdi-alert-circle"
      color="warning"
      lines="one"
    >
      <v-banner-text> Newer table data is available. </v-banner-text>
      <template #actions>
        <v-btn variant="text" @click="handleRefresh">Refresh</v-btn>
      </template>
    </v-banner>
    <v-data-table-server
      v-model="selectedItems"
      v-model:sort-by="sortBy"
      v-model:page="page"
      v-model:items-per-page="itemsPerPage"
      show-select
      return-object
      multi-sort
      :items-per-page-options="itemsPerPageOptions"
      :items-length="totalItems"
      :headers="headers"
      :items="items"
      density="compact"
      item-key="name"
      @update:options="callLoadItems"
    >
      <!--
            For information about specific header slots
            see: https://vuetifyjs.com/en/api/v-data-table-server/#slots
            -->
      <template
        v-for="header in headers"
        :key="header.value"
        #[`header.${header.value}`]="{ column, isSorted, sortBy: tableSortBy }"
      >
        <div
          style="display: flex; align-items: center"
          :width="column.width"
          :aria-sort="sortDirection(header.value, isSorted, tableSortBy)"
        >
          <!-- Display text -->
          <span>{{ header.title }}</span>

          <!-- up/down badge for sorting -->
          <v-icon v-if="header.sortable" class="ms-1">
            {{ sortIcon(header.value, isSorted, tableSortBy) }}
          </v-icon>

          <!-- number badge for sorting precedence -->
          <span
            v-if="header.sortable && sortNumber(header.value, tableSortBy)"
            class="v-badge ms-1"
            style="font-size: 0.75em; color: #1976d2"
          >
            {{ sortNumber(header.value, isSorted, tableSortBy) }}
          </span>
          <!-- filter badge -->
          <v-menu
            v-if="header.filterable"
            v-model="activeFilterEdit[header.value]"
            :close-on-content-click="false"
          >
            <template #activator="{ props: activatorProps }">
              <v-icon v-bind="activatorProps" small class="ms-1">
                {{ header.filterModel ? 'mdi-filter-variant-plus' : 'mdi-filter-variant' }}
              </v-icon>
            </template>
            <v-card>
              <slot
                :name="`filter-input.${header.value}`"
                :header="header"
                :on-filter-change="onFilterChange"
              >
                <!-- The clear button does not always emit an input event -->
                <v-text-field
                  v-model="header.filterModel"
                  :label="`Filter by ${header.title}`"
                  clearable
                  dense
                  hide-details
                  @input="onFilterChange"
                  @click:clear="onFilterChange"
                  @keydown.enter="setShowFilter(header, false)"
                />
              </slot>
            </v-card>
          </v-menu>
        </div>
      </template>

      <!-- Customize the contents of the "actions" column for every row. -->
      <template #[`item.actions`]="{ item, index }">
        <div class="action-icons">
          <slot name="more-action-icons" :item="item" :index="index"> </slot>
          <v-icon size="small" @click="openDeleteDialog(item, index)">mdi-delete</v-icon>
        </div>
      </template>
    </v-data-table-server>

    <slot name="more-selected-items-buttons" :selected-item-count="selectedItemCount"> </slot>

    <v-btn
      class="ma-2"
      size="large"
      :disabled="selectedItemCount === 0"
      @click="deleteSelectedItems"
    >
      Delete Selected
    </v-btn>
    <v-btn class="ma-2" size="large" @click="handleRefresh">Refresh</v-btn>

    <slot name="more-action-dialogs" :selected-item-count="selectedItemCount"> </slot>

    <confirmation-dialog
      v-model:active="activeConfirmDelete"
      @canceled="cancelDelete"
      @confirmed="confirmDelete"
    >
      <slot name="delete-dialog-text">Are you sure you want to delete this item?</slot>
    </confirmation-dialog>

    <confirmation-dialog
      v-model:active="activeConfirmDeleteSelected"
      @canceled="closeDeleteSelected"
      @confirmed="applyDeleteSelected"
    >
      Are you sure you want to delete {{ selectedItemCount }} selected items?
    </confirmation-dialog>
  </div>
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  defineEmits,
  defineProps,
  defineModel,
  onMounted,
  onBeforeUnmount,
  nextTick
} from 'vue'
import ConfirmationDialog from '../common/ConfirmationDialog.vue'
import logger from '@/common/Logger'

// Use defineModel for v-model bindings
/**
 * The currently selected items in the data table.
 * @model
 * @type {Array}
 */
const selectedItems = defineModel('selectedItems', { type: Array })
/**
 * The sorting criteria for the data table.
 * @model
 * @type {Array}
 */
const sortBy = defineModel('sortBy', { type: Array })
/**
 * The current page number.
 * @model
 * @type {Number}
 */
const page = defineModel('page', { type: Number })
/**
 * The number of items to display per page.
 * @model
 * @type {Number}
 */
const itemsPerPage = defineModel('itemsPerPage', { type: Number })
/**
 * The total number of items in the data table.
 * @model
 * @type {Number}
 */
const totalItems = defineModel('totalItems', { type: Number })
/**
 * The items to display in the data table.
 * @model
 * @type {Array}
 */
const items = defineModel('items', { type: Array })
/**
 * The currently active filter edit state.
 * @model
 * @type {Object}
 */
const activeFilterEdit = defineModel('activeFilterEdit', { type: Object })
/**
 * A flag to indicate that the table should be reloaded.
 * @model
 * @type {Boolean}
 */
const shouldRefresh = defineModel('shouldRefresh', { type: Boolean })

/**
 * @property {Array} headers The headers for the data table.
 * @property {Array} itemsPerPageOptions The options for the number of items to display per page.
 * @property {Function} deleteSingleItem The function to call when a document is deleted.
 * @property {Function} deleteMultipleItems The function to call when multiple documents are deleted.
 * @property {Function} loadItems The function to call to load the items for the data table.
 * @property {Function} loadTableStats The function to call to load the stats for the data table.
 */
const props = defineProps({
  headers: {
    type: Array,
    default: () => []
  },
  itemsPerPageOptions: {
    type: Array,
    default: () => [10, 25, 50]
  },
  deleteSingleItem: {
    type: Function,
    default: () => async (/* id */) => {}
  },
  deleteMultipleItems: {
    type: Function,
    default: () => async (/* ids */) => {}
  },
  loadItems: {
    type: Function,
    default: () => async () => ({ totalItems: 0, items: [], tableUpdatedTime: null })
  },
  loadTableStats: {
    type: Function,
    default: () => async () => ({ totalItems: 0, tableUpdatedTime: null })
  }
})

/**
 * Defines the events emitted by the component.
 * @emits confirmDelete - When the user confirms a delete action.
 */
defineEmits(['confirmDelete'])

const targetItem = ref({})

const selectedItemCount = computed(() => {
  return selectedItems.value.length
})

//
// Sorting
//

/**
 *
 */
function sortDirection(columnKey, isSorted, sortBy) {
  if (isSorted) {
    if (Array.isArray(sortBy)) {
      const matched = sortBy.find((s) => s.key === columnKey)
      if (matched) {
        return matched?.order === 'desc' ? 'descending' : 'ascending'
      }
    } else if (sortBy && sortBy.key) {
      if (sortBy?.key === columnKey) {
        return sortBy?.order === 'desc' ? 'descending' : 'ascending'
      }
    }
  }
  return 'none'
}

/**
 *
 */
function sortIcon(columnKey, isSorted, sortBy) {
  if (isSorted) {
    const direction = sortDirection(columnKey, isSorted, sortBy)
    if (direction === 'descending') {
      return 'mdi-arrow-down'
    } else if (direction === 'ascending') {
      return 'mdi-arrow-up'
    }
  }
  return 'mdi-swap-vertical'
}

/**
 *
 */
function sortNumber(columnKey, isSorted, sortBy) {
  if (isSorted) {
    if (Array.isArray(sortBy)) {
      const matchedIndex = sortBy.findIndex((s) => s.key === columnKey)
      if (matchedIndex >= 0) {
        return matchedIndex + 1
      }
    } else if (sortBy && sortBy.key) {
      if (sortBy?.key === columnKey) {
        return 1
      }
    }
  }
  return null
}

//
// Filtering
//

function setShowFilter(header, val) {
  activeFilterEdit.value[header.value] = val
}

async function onFilterChange() {
  await nextTick()

  await handleRefresh()
}

//
// Refresh
//

// Internal state for table freshness
const tableOutdated = ref(false)
const tableUpdatedAt = ref()

/**
 * Refresh
 */
async function handleRefresh() {
  logger.info('refreshing - calling load item')
  await callLoadItems()

  shouldRefresh.value = false
}

/**
 * Watches the `shouldRefresh` model property for changes.
 * When `shouldRefresh` is set to `true`, this watcher triggers a refresh of the table data
 * by calling `callLoadItems`. After the data is loaded, it resets `shouldRefresh` to `false`.
 * This allows parent components to programmatically trigger a data reload.
 * @param {boolean} newVal The new value of `shouldRefresh`.
 * @param {boolean} _oldVal The old value of `shouldRefresh`.
 */
watch(shouldRefresh, async (newVal, _oldVal) => {
  if (newVal) {
    await nextTick()

    await handleRefresh()
  }
})

//
// Delete
//

const activeConfirmDelete = ref(false)

/**
 * Opens the delete confirmation dialog for a specific item.
 * @param {Object} item - The item to delete
 */
function openDeleteDialog(item) {
  targetItem.value = { ...item }
  activeConfirmDelete.value = true
}

/**
 * Handles confirmation of delete dialog by applying the delete operation.
 */
async function confirmDelete() {
  if (props.deleteSingleItem) {
    await props.deleteSingleItem(targetItem.value)
  }
  await closeDeleteDialog()
}

/**
 * Handles cancellation of delete dialog by applying the delete operation.
 */
async function cancelDelete() {
  await closeDeleteDialog()
}

/**
 * Closes the delete confirmation dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeDeleteDialog() {
  await handleRefresh()

  targetItem.value = {}
  activeConfirmDelete.value = false
}

//
// Confirmation dialog for deletion of selected files
//
const activeConfirmDeleteSelected = ref(false)

/**
 * Opens the confirmation dialog for deleting multiple selected documents.
 * Displays a confirmation prompt before proceeding with batch deletion.
 */
function deleteSelectedItems() {
  activeConfirmDeleteSelected.value = true
}

/**
 * Applies the batch deletion operation after user confirmation.
 * Calls the deleteSelectedDocuments function to process all selected items.
 */
async function applyDeleteSelected() {
  await props.deleteMultipleItems([...selectedItems.value])

  // Clear the selections
  selectedItems.value = []
}

/**
 * Closes the batch delete confirmation dialog and refreshes the table data.
 * Called after the batch deletion operation completes.
 */
async function closeDeleteSelected() {
  await handleRefresh()
}

//
// Load
//
const loading = ref(false)

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
    loading.value = true
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
  } finally {
    loading.value = false
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
