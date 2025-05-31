<template>
  <v-banner
    v-if="tableOutdated"
    class="pa-2 ma-2"
    icon="mdi-alert-circle"
    color="warning"
    lines="one"
  >
    <v-banner-text> Newer table data is available. </v-banner-text>

    <template #actions>
      <v-btn variant="text" @click="loadItems">Refresh</v-btn>
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
    :headers="tableHeaders"
    :items="items"
    density="compact"
    item-key="name"
    @update:options="loadItems"
  >
    <template #item.actions="{ item, index }">
      <div class="action-icons">
        <v-icon class="me-2" size="small" @click="editItem(item, index)"> mdi-pencil </v-icon>
        <v-icon size="small" @click="deleteItem(item, index)"> mdi-delete </v-icon>
      </div>
    </template>
  </v-data-table-server>
  <v-btn class="ma-2" size="large" @click="addDocSet">Add New</v-btn>
  <v-btn class="ma-2" size="large" @click="loadItems">Refresh</v-btn>
  <add-doc-set-dialog
    v-model:active="activeAddDocSet"
    v-model="targetItem"
    @done="closeAddDocSet"
    @confirmed="applyAddDocSet"
  >
  </add-doc-set-dialog>
  <edit-doc-set-dialog
    v-model:active="activeEditDocSet"
    v-model="targetItem"
    @done="closeEditDocSet"
    @confirmed="applyEditDocSet"
  >
  </edit-doc-set-dialog>
  <confirmation-dialog
    v-model:active="activeConfirmDelete"
    @done="closeDeleteItem"
    @confirmed="applyDeleteItem"
  >
    Are you sure you want to delete this item?
  </confirmation-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, toRaw, watch } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import { useDocumentSetStore } from './DocSetStore'
import ConfirmationDialog from '../common/ConfirmationDialog.vue'
import AddDocSetDialog from './AddDocSetDialog.vue'
import EditDocSetDialog from './EditDocSetDialog.vue'
import logger from '../common/Logger.js'

const currentUserStore = useCurrentUserStore()
const documentSetStore = useDocumentSetStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)
const { page, itemsPerPage, totalItems, items, selectedItems } = storeToRefs(documentSetStore)
const tableUpdatedAt = ref()
const tableOutdated = ref(false)

const loading = ref(false)

const tableHeaders = ref([
  {
    title: 'Document Set',
    key: 'name',
    width: '150px',
    sortable: true
  },
  { title: 'Is Public', value: 'isPublicViewable', sortable: true },
  { title: 'Is Default', key: 'isNewDocDefault', sortable: true },
  {
    title: 'Last Modified Date',
    key: 'modificationTime',
    sortable: false
  },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false }
])

const sortBy = ref([])

watch(sortBy, async (newValue, _oldValue) => {
  logger.debug('Sort criteria changed', {
    newSort: newValue,
    oldSort: _oldValue
  })
})

const itemsPerPageOptions = [
  { value: 2, title: '2' },
  { value: 5, title: '5' },
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' }
]

const selectedItemCount = computed(() => {
  return selectedItems.value.length
})

const targetIndex = ref(-1)
const targetItem = ref({})

//
// Add new document-set dialog
//
const activeAddDocSet = ref(false)

/**
 * Opens the dialog for adding a new document set.
 * Initializes the target item with default values for a new document set.
 */
function addDocSet() {
  activeAddDocSet.value = true

  targetIndex.value = -1
  targetItem.value = {
    name: '',
    isPublicViewable: true,
    isNewDocDefault: false
  }
}

/**
 * Applies the add document set operation after user confirmation.
 * Calls the addDocumentSet function to create the new document set.
 */
async function applyAddDocSet() {
  await addDocumentSet()
}

/**
 * Sends a request to the server to create a new document set.
 * Uses the values from the target item to populate the new document set properties.
 */
async function addDocumentSet() {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const body = {
      name: targetItem.value.name,
      isNewDocDefault: targetItem.value.isNewDocDefault,
      isPublicViewable: targetItem.value.isPublicViewable
    }

    const response = await fetch('/api/document-sets/', {
      method: 'POST',
      headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error('Add failed')
    }

    await response.json()
    logger.apiSuccess('Document set added', { name: targetItem.value.name })
  } catch (error) {
    logger.apiError('Document set add failed', error, { name: targetItem.value.name })
  }
}

/**
 * Closes the add document set dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeAddDocSet() {
  await loadItems()

  nextTick(() => {
    targetItem.value = {}
    targetIndex.value = -1
  })
}

//
// Edit document-set dialog
//
const activeEditDocSet = ref(false)

/**
 * Opens the edit dialog for a specific document set.
 * @param {Object} item - The document set item to be edited
 * @param {number} index - The index of the item in the table
 */
function editItem(item, index) {
  activeEditDocSet.value = true
  targetIndex.value = index
  targetItem.value = Object.assign({}, item)

  logger.debug('Edit document set dialog opened', {
    docSetName: targetItem.value.name,
    docSetId: targetItem.value.id
  })
}

/**
 * Applies the edit document set operation after user confirmation.
 * Calls the editDocumentSet function with the target item's ID.
 */
async function applyEditDocSet() {
  await editDocumentSet(targetItem.value.id)
}

/**
 * Sends a request to the server to update an existing document set.
 * @param {string} doc_set_uuid - The unique identifier of the document set to edit
 */
async function editDocumentSet(doc_set_uuid) {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const body = {
      isNewDocDefault: targetItem.value.isNewDocDefault,
      isPublicViewable: targetItem.value.isPublicViewable
    }

    logger.debug('Editing document set', { docSetId: doc_set_uuid, changes: body })

    const response = await fetch(`/api/document-sets/${doc_set_uuid}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error('Edit failed')
    }

    await response.json()
    logger.apiSuccess('Document set edited', { docSetId: doc_set_uuid })
  } catch (error) {
    logger.apiError('Document set edit failed', error, { docSetId: doc_set_uuid })
  }
}

/**
 * Closes the edit document set dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeEditDocSet() {
  await loadItems()

  nextTick(() => {
    targetItem.value = {}
    targetIndex.value = -1
  })
}

//
// Confirmation dialog for single deletion
//

const activeConfirmDelete = ref(false)

/**
 * Opens the confirmation dialog for deleting a document set.
 * @param {Object} item - The document set item to be deleted
 * @param {number} index - The index of the item in the table
 */
function deleteItem(item, index) {
  activeConfirmDelete.value = true
  targetIndex.value = index
  targetItem.value = Object.assign({}, item)
}

/**
 * Applies the deletion operation after user confirmation.
 * Calls the deleteDocumentSet function with the target item's ID.
 */
async function applyDeleteItem() {
  await deleteDocumentSet(targetItem.value.id)
}

/**
 * Sends a request to the server to delete a specific document set.
 * @param {string} doc_set_uuid - The unique identifier of the document set to delete
 */
async function deleteDocumentSet(doc_set_uuid) {
  try {
    const headers = {
      Accept: 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const response = await fetch(`/api/document-sets/${doc_set_uuid}`, {
      method: 'DELETE',
      headers
    })

    if (!response.ok) {
      throw new Error('Delete failed')
    }

    await response.json()
    logger.apiSuccess('Document set deleted', { docSetId: doc_set_uuid })
  } catch (error) {
    logger.apiError('Document set deletion failed', error, { docSetId: doc_set_uuid })
  }
}

/**
 * Closes the delete confirmation dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeDeleteItem() {
  await loadItems()

  nextTick(() => {
    targetItem.value = {}
    targetIndex.value = -1
  })
}

//
// Polling for server table updates.
//

let intervalId = null

onMounted(async () => {
  await loadItems()

  intervalId = setInterval(async () => {
    await loadTableStats()
  }, 30000)
})

onBeforeUnmount(async () => {
  clearInterval(intervalId)
  intervalId = null
})

/**
 * Loads table statistics from the server to check for document set updates.
 * Updates the total item count and tracks when the table was last modified to show refresh notifications.
 */
async function loadTableStats() {
  try {
    const headers = {
      Accept: 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const response = await fetch('/api/document-sets/stats', {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      throw new Error('Getting table stats failed')
    }

    const data = await response.json()

    totalItems.value = data.documentSetCount
    if (tableUpdatedAt.value !== data.tableUpdatedTime) {
      tableOutdated.value = true
      tableUpdatedAt.value = data.tableUpdatedTime
    }
  } catch (error) {
    console.error('Error getting table stats:', error)
  }
}

//
// Loading data from server
//

/**
 * Loads document set data from the server with pagination and sorting support.
 * Fetches document sets based on current page, items per page, and sort criteria, then updates the table display.
 */
async function loadItems() {
  loading.value = true

  try {
    const params = new URLSearchParams({
      // VDataTableServer's page is 1-indexed. The backend API's page is 0-indexed.
      page: page.value - 1,
      itemsPerPage: itemsPerPage.value
    })

    if (sortBy.value.length > 0) {
      const sortByParam = sortBy.value
        .map((item) => {
          let key = item.key
          if (item.order === 'desc') {
            key = '-' + key
          }
          return key
        })
        .join(',')

      params.append('sortBy', sortByParam)
    }

    const headers = {
      Accept: 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const response = await fetch(`/api/document-sets/?${params}`, {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      throw new Error('Failed to get files')
    }

    const data = await response.json()

    totalItems.value = data.documentSetCount
    tableUpdatedAt.value = data.tableUpdatedTime
    tableOutdated.value = false
    items.value = data.documentSets.map((item) => toRaw(item))
  } catch (error) {
    totalItems.value = 0
    tableOutdated.value = false
    items.value = []
    loading.value = false
    console.error('Error getting files:', error)
  }
  loading.value = false
}
</script>

<style>
.action-icons {
  display: flex;
  gap: 4px; /* Adjust spacing as needed */
  white-space: nowrap; /* Prevents wrapping */
}
</style>
