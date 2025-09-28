<template>
  <common-data-table
    v-model:total-items="totalItems"
    v-model:items="items"
    v-model:sort-by="sortBy"
    v-model:page="page"
    v-model:items-per-page="itemsPerPage"
    v-model:selected-items="selectedItems"
    :headers="headers"
    :items-per-page-options="itemsPerPageOptions"
    :active-filter-edit="activeFilterEdit"
    :delete-single-item="deleteSingleDocumentSet"
    :delete-multiple-items="deleteMultipleDocumentSets"
    :load-items="loadItems"
    :load-table-stats="loadTableStats"
    :should-refresh="shouldRefresh"
  >
    <template #delete-dialog-text> Are you sure you want to delete this item? </template>

    <template #more-action-icons="{ item, index }">
      <v-icon class="me-2" size="small" @click="openEditDialog(item, index)">mdi-pencil</v-icon>
    </template>
    <template #more-selected-items-buttons="{ selectedItemCount }">
      <v-btn class="ma-2" size="large" @click="addDocSet">Add New</v-btn>
    </template>
    <template #more-action-dialogs="{ selectedItemCount }">
      <edit-doc-set-dialog
        v-model:active="activeEditDocSet"
        v-model="targetDocSet"
        @canceled="closeEditDocSet"
        @confirmed="applyEditDocSet"
      >
      </edit-doc-set-dialog>

      <add-doc-set-dialog
        v-model:active="activeAddDocSet"
        v-model="newDocSet"
        @canceled="closeAddDocSet"
        @confirmed="applyAddDocSet"
      >
      </add-doc-set-dialog>
    </template>
  </common-data-table>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, toRaw } from 'vue'
import { storeToRefs } from 'pinia'

import CommonDataTable from '../common/CommonDataTable.vue'
import { getAuthorization } from '../common/AuthUtils.js'
import { useDocumentSetStore } from './DocSetStore'
import AddDocSetDialog from './AddDocSetDialog.vue'
import EditDocSetDialog from './EditDocSetDialog.vue'
import logger from '../common/Logger.js'

const documentSetStore = useDocumentSetStore()

const { page, itemsPerPage, totalItems, items, selectedItems } = storeToRefs(documentSetStore)

const shouldRefresh = ref(false)

const headers = ref([
  {
    title: 'Document Set',
    value: 'name',
    width: '150px',
    sortable: true
  },
  { title: 'Is Public', value: 'isPublicViewable', sortable: true },
  { title: 'Is Default', value: 'isNewDocDefault', sortable: true },
  {
    title: 'Last Modified Date',
    value: 'modificationTime',
    sortable: false
  },
  { title: 'Status', value: 'status', sortable: true },
  { title: 'Actions', value: 'actions', sortable: false }
])

const sortBy = ref([])

const itemsPerPageOptions = [
  { value: 2, title: '2' },
  { value: 5, title: '5' },
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' }
]

const activeFilterEdit = ref({})

//
// Add new document-set dialog
//
const activeAddDocSet = ref(false)
const newDocSet = ref(null)

/**
 * Opens the dialog for adding a new document set.
 * Initializes the target item with default values for a new document set.
 */
function addDocSet() {
  activeAddDocSet.value = true

  newDocSet.value = {
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

  shouldRefresh.value = true
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
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const body = {
      name: newDocSet.value.name,
      isNewDocDefault: newDocSet.value.isNewDocDefault,
      isPublicViewable: newDocSet.value.isPublicViewable
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
    logger.apiSuccess('Document set added', { name: newDocSet.value.name })
  } catch (error) {
    logger.apiError('Document set add failed', error, { name: newDocSet.value.name })
  }
}

/**
 * Closes the add document set dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeAddDocSet() {
  shouldRefresh.value = true

  newDocSet.value = {}
}

//
// Edit document-set dialog
//
const targetDocSet = ref(null)
const activeEditDocSet = ref(false)

/**
 * Opens the edit dialog for a specific document set.
 * @param {Object} item - The document set item to be edited
 * @param {number} index - The index of the item in the table
 */
function openEditDialog(item, _index) {
  activeEditDocSet.value = true
  targetDocSet.value = Object.assign({}, item)
}

/**
 * Applies the edit document set operation after user confirmation.
 * Calls the editDocumentSet function with the target item's ID.
 */
async function applyEditDocSet() {
  await editDocumentSet(targetDocSet.value.id)
  logger.info('edited doc set')

  await closeEditDocSet()
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
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const body = {
      name: targetDocSet.value.name,
      isNewDocDefault: targetDocSet.value.isNewDocDefault,
      isPublicViewable: targetDocSet.value.isPublicViewable
    }

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
  shouldRefresh.value = true
  targetDocSet.value = {}
}

//
// Single deletion
//

/**
 * Sends a request to the server to delete a specific document set.
 * @param {string} docSetUuid - The unique identifier of the document set to delete
 */
async function deleteSingleDocumentSet(docSetUuid) {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const response = await fetch(`/api/document-sets/${docSetUuid}`, {
      method: 'DELETE',
      headers
    })

    if (!response.ok) {
      throw new Error('Delete failed')
    }

    await response.json()
    logger.apiSuccess('Document set deleted', { docSetId: docSetUuid })
  } catch (error) {
    logger.apiError('Document set deletion failed', error, { docSetId: docSetUuid })
  }
}

//
// Multiple deletions
//

/**
 * Sends a request to the server to delete a specific document set.
 * @param {string} doc_set_uuid - The unique identifier of the document set to delete
 */
async function deleteMultipleDocumentSets(docSetUuids) {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    for (const docSetUuid of docSetUuids) {
      const response = await fetch(`/api/document-sets/${docSetUuid}`, {
        method: 'DELETE',
        headers
      })

      if (!response.ok) {
        throw new Error(`Delete failed for doc-set ${docSetUuid}`)
      }

      await response.json()
      logger.apiSuccess('Document set deleted', { docSetId: docSetUuid })
    }
  } catch (error) {
    logger.apiError('Document set deletion failed', error, { docSetUuids: docSetUuids })
  }
}

//
// Polling for server table updates.
//

let intervalId = null

onMounted(async () => {
  shouldRefresh.value = true

  intervalId = setInterval(async () => {
    await loadTableStats()
  }, 30000)
})

onBeforeUnmount(() => {
  clearInterval(intervalId)
  intervalId = null
})

/**
 * Loads table statistics from the server to check for document set updates.
 * Updates the total item count and tracks when the table was last modified to show refresh notifications.
 */
async function loadTableStats() {
  const headers = {
    Accept: 'application/json'
  }
  const auth = await getAuthorization()
  if (auth) {
    headers.Authorization = auth
  } else {
    // Return "mock" data. Reduces unauthorized-access errors seen on the API server.
    return {
      totalItems: 0,
      items: [],
      tableUpdatedTime: '1970-01-01T00:00:00Z'
    }
  }

  const response = await fetch('/api/document-sets/stats', {
    method: 'GET',
    headers
  })

  if (!response.ok) {
    throw new Error('Getting table stats failed')
  }

  const data = await response.json()

  return {
    totalItems: data.documentSetCount,
    tableUpdatedTime: data.tableUpdatedTime
  }
}

//
// Load data from server
//

/**
 * Loads document set data from the server with pagination and sorting support.
 * Fetches document sets based on current page, items per page, and sort criteria, then updates the table display.
 */
async function loadItems() {
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
          key = `-${key}`
        }
        return key
      })
      .join(',')

    params.append('sortBy', sortByParam)
  }

  const headers = {
    Accept: 'application/json'
  }
  const auth = await getAuthorization()
  if (auth) {
    headers.Authorization = auth
  } else {
    // Return "mock" data. Reduces unauthorized-access errors seen on the API server.
    return {
      totalItems: 0,
      items: [],
      tableUpdatedTime: '1970-01-01T00:00:00Z'
    }
  }

  const response = await fetch(`/api/document-sets/?${params}`, {
    method: 'GET',
    headers
  })

  if (!response.ok) {
    throw new Error('Failed to get document sets')
  }

  const data = await response.json()

  return {
    totalItems: data.documentSetCount,
    items: data.documentSets.map((item) => toRaw(item)),
    tableUpdatedTime: data.tableUpdatedTime
  }
}
</script>

<style>
.action-icons {
  display: flex;
  gap: 4px; /* Adjust spacing as needed */
  white-space: nowrap; /* Prevents wrapping */
}
</style>
