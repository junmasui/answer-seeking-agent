<template>
  <common-data-table
    v-model:total-items="totalItems"
    v-model:items="items"
    v-model:sort-by="sortBy"
    v-model:page="page"
    v-model:items-per-page="itemsPerPage"
    v-model:selected-items="selectedItems"
    v-model:should-reload="shouldReload"
    :headers="headers"
    :items-per-page-options="itemsPerPageOptions"
    :active-filter-edit="activeFilterEdit"
    :edit-document="editDocument"
    :delete-document="deleteDocument"
    :load-items="loadItems"
    :load-table-stats="loadTableStats"
    @refresh="loadItems"
  >
    <!-- Templates of Usability -->

    <template #edit-dialog-text> Are you sure you want to edit this item? </template>
    <template #delete-dialog-text> Are you sure you want to delete this item? </template>
  </common-data-table>
  <v-btn class="ma-2" size="large" :disabled="selectedItemCount === 0" @click="ingestSelectedItems"
    >Ingest Selected</v-btn
  >
  <v-btn class="ma-2" size="large" :disabled="totalItems === 0" @click="ingestAllUploaded"
    >Ingest All Uploaded</v-btn
  >
  <v-btn class="ma-2" size="large" :disabled="selectedItemCount === 0" @click="deleteSelectedItems"
    >Delete Selected</v-btn
  >
  <v-btn class="ma-2" size="large" @click="loadItems">Refresh</v-btn>

  <confirmation-dialog
    v-model:active="activeConfirmIngestItem"
    @done="closeIngestItem"
    @confirmed="applyIngestItem"
  >
    Are you sure you want to ingest this item?
  </confirmation-dialog>
  <confirmation-dialog
    v-model:active="activeConfirmIngestAllUploaded"
    @done="closeIngestAllUploaded"
    @confirmed="applyIngestAllUploaded"
  >
    Are you sure you want to ingest all uploaded items?
  </confirmation-dialog>
  <confirmation-dialog
    v-model:active="activeConfirmDeleteSelected"
    @canceled="closeDeleteSelected"
    @confirmed="applyDeleteSelected"
  >
    Are you sure you want to delete {{ selectedItemCount }} selected items?
  </confirmation-dialog>
  <confirmation-dialog
    v-model:active="activeConfirmIngestSelected"
    @canceled="closeIngestSelected"
    @confirmed="applyIngestSelected"
  >
    Are you sure you want to ingest {{ selectedItemCount }} selected items?
  </confirmation-dialog>
</template>

<script setup>
import CommonDataTable from '../common/CommonDataTable.vue'
import { ref, computed, nextTick, toRaw } from 'vue'
import { storeToRefs } from 'pinia'
import { getAuthorization } from '../common/AuthUtils.js'
import { useDocumentStore } from './DocStore'
import ConfirmationDialog from '../common/ConfirmationDialog.vue'
import logger from '../common/Logger.js'

const documentStore = useDocumentStore()

const {
  page,
  itemsPerPage,
  totalItems,
  items,
  selectedItems,
  documentSetFilter,
  contentTypeFilter,
  sourceUrlFilter
} = storeToRefs(documentStore)
const loading = ref(false)

const headers = ref([
  {
    title: 'File Name',
    value: 'name',
    width: '500px',
    sortable: true
  },
  { title: 'Size', value: 'sizeBytes', width: '100px', sortable: true },
  {
    title: 'Document Set',
    value: 'documentSetName',
    width: '150px',
    sortable: true,
    filterable: true,
    filterModel: documentSetFilter,
    onFilterChange: onDocumentSetFilterChange
  },
  {
    title: 'Source URL',
    value: 'sourceUrl',
    width: '300px',
    sortable: false,
    filterable: true,
    filterModel: sourceUrlFilter,
    onFilterChange: onSourceUrlFilterChange
  },
  {
    title: 'Content Type',
    value: 'contentType',
    width: '50px',
    sortable: true,
    filterable: true,
    filterModel: contentTypeFilter,
    onFilterChange: onContentTypeFilterChange
  },
  { title: 'Status', value: 'status', width: '50px', sortable: true },
  {
    title: 'Ingestion Date',
    value: 'ingestionTime',
    width: '150px',
    sortable: true
  },
  {
    title: 'Last Modified Date',
    key: 'modificationTime',
    width: '150px',
    sortable: true
  },
  {
    title: 'Download Date',
    value: 'downloadTimeUtc',
    width: '150px',
    sortable: true
  },
  { title: 'Actions', value: 'actions', width: '50px', sortable: false }
])

const sortBy = ref([])

const itemsPerPageOptions = [
  { value: 2, title: '2' },
  { value: 5, title: '5' },
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' }
]

const selectedItemCount = computed(() => {
  return selectedItems.value.length
})

const targetIndex = ref(-1)
const targetItem = ref({})

const activeFilterEdit = ref({})
const shouldReload = ref(false)

//
// Confirmation dialog for one-file ingestion
//

const activeConfirmIngestItem = ref(false)

/**
 * Opens the confirmation dialog for ingesting a single document.
 * @param {Object} item - The document item to be ingested
 * @param {number} index - The index of the item in the table
 */
function ingestItem(item, index) {
  activeConfirmIngestItem.value = true
  targetIndex.value = index
  targetItem.value = Object.assign({}, item)
}

/**
 * Applies the ingestion operation after user confirmation.
 * Calls the ingestDocument function with the target item's ID.
 */
async function applyIngestItem() {
  await ingestDocument(targetItem.value.id)
}

/**
 * Sends a request to the server to ingest a specific document.
 * @param {string} doc_uuid - The unique identifier of the document to ingest
 */
async function ingestDocument(doc_uuid) {
  try {
    const headers = {
      Accept: 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }
    const response = await fetch('/api/documents/ingest', {
      method: 'POST',
      headers
    })

    if (!response.ok) {
      throw new Error('Ingest failed')
    }

    await response.json()
    logger.apiSuccess('Document ingest queued', { docId: doc_uuid })
  } catch (error) {
    console.error('Error ingesting:', error)
  }
}

/**
 * Closes the ingest confirmation dialog and refreshes the table data.
 * Resets the target item and index after the operation completes.
 */
async function closeIngestItem() {
  await loadItems()

  nextTick(() => {
    targetItem.value = {}
    targetIndex.value = -1
  })
}

//
// Confirmation dialog for ingestion of all uploaded files
//

const activeConfirmIngestAllUploaded = ref(false)

/**
 * Opens the confirmation dialog for ingesting all uploaded documents.
 * Displays a confirmation prompt before proceeding with full batch ingestion.
 */
function ingestAllUploaded() {
  activeConfirmIngestAllUploaded.value = true
}

/**
 * Applies the operation to ingest all uploaded documents after user confirmation.
 * Calls the ingestAllUploadedDocuments function to process all uploaded files.
 */
async function applyIngestAllUploaded() {
  await ingestAllUploadedDocuments()
}

/**
 * Sends a request to the server to ingest all documents with uploaded status.
 * Processes all uploaded documents regardless of current selection state.
 */
async function ingestAllUploadedDocuments() {
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
      allUploaded: true
    }

    const response = await fetch('/api/documents/ingest', {
      method: 'POST',
      headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error('Ingest failed')
    }

    await response.json()
    logger.apiSuccess('All uploaded documents ingest queued')
  } catch (error) {
    console.error('Error ingesting:', error)
  }
}

/**
 * Closes the ingest all confirmation dialog and refreshes the table data.
 * Called after the batch ingestion operation completes.
 */
async function closeIngestAllUploaded() {
  await loadItems()
}

/**
 * Placeholder function for editing a document.
 * @param {string} _doc_uuid - The unique identifier of the document to edit (unused in placeholder implementation)
 */
async function editDocument(_doc_uuid) {
  // Simulate the delay from a real call to the API Server.
  await new Promise((resolve) => setTimeout(resolve, 100))
}

/**
 * Sends a request to the server to delete a specific document.
 * @param {string} doc_uuid - The unique identifier of the document to delete
 */
async function deleteDocument(doc_uuid) {
  try {
    const headers = {
      Accept: 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const response = await fetch(`/api/documents/${doc_uuid}`, {
      method: 'DELETE',
      headers
    })

    if (!response.ok) {
      throw new Error('Delete failed')
    }

    await response.json()
    logger.apiSuccess('Document deleted', { docId: doc_uuid })
  } catch (error) {
    console.error('Error deleting:', error)
  }
}

//
// Confirmation dialog for ingestion of selected files
//

const activeConfirmIngestSelected = ref(false)

/**
 * Opens the confirmation dialog for ingesting multiple selected documents.
 * Displays a confirmation prompt before proceeding with batch ingestion.
 */
function ingestSelectedItems() {
  activeConfirmIngestSelected.value = true
}

/**
 * Applies the batch ingestion operation after user confirmation.
 * Calls the ingestSelectedDocuments function to process all selected items.
 */
async function applyIngestSelected() {
  await ingestSelectedDocuments()
}

/**
 * Sends a request to the server to ingest all currently selected documents.
 * Clears the selection after successful ingestion and logs the operation.
 */
async function ingestSelectedDocuments() {
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
      docUuids: selectedItems.value.map((x) => x.id)
    }

    const response = await fetch('/api/documents/ingest', {
      method: 'POST',
      headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error('Ingest failed')
    }

    // Clear the selections
    selectedItems.value = []

    await response.json()
    logger.apiSuccess('Selected documents ingest queued', { count: body.docUuids.length })
  } catch (error) {
    console.error('Error ingesting:', error)
  }
}

/**
 * Closes the batch ingest confirmation dialog and refreshes the table data.
 * Called after the batch ingestion operation completes.
 */
async function closeIngestSelected() {
  await loadItems()
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
  await deleteSelectedDocuments()
}

/**
 * Sends a request to the server to delete all currently selected documents.
 * Clears the selection after successful deletion and logs the operation.
 */
async function deleteSelectedDocuments() {
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
      docUuids: selectedItems.value.map((x) => x.id)
    }

    const response = await fetch('/api/documents/delete', {
      method: 'POST',
      headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error('Delete failed')
    }

    // Clear the selections
    selectedItems.value = []

    await response.json()
    logger.apiSuccess('Selected documents deleted', { count: body.docUuids.length })
  } catch (error) {
    console.error('Error deleteing:', error)
  }
}

/**
 * Closes the batch delete confirmation dialog and refreshes the table data.
 * Called after the batch deletion operation completes.
 */
async function closeDeleteSelected() {
  await loadItems()
}

/**
 * Loads table statistics from the server to check for data updates.
 * Updates the total item count and tracks when the table was last modified to show refresh notifications.
 */
async function loadTableStats() {
  const headers = {
    Accept: 'application/json'
  }
  const auth = await getAuthorization()
  if (auth) {
    headers.Authorization = auth
  }

  const response = await fetch('/api/documents/stats', {
    method: 'GET',
    headers
  })

  if (!response.ok) {
    throw new Error('Getting table stats failed')
  }

  const data = await response.json()

  return {
    totalItems: data.documentCount,
    tableUpdatedTime: data.tableUpdatedTime
  }
}

//
// Loading data from server
//

async function onDocumentSetFilterChange() {
  logger.debug(`on document set filter change ${documentSetFilter.value}`)
  // Notify the child that data should be reloaded
  shouldReload.value = true
}

async function onContentTypeFilterChange() {
  logger.debug(`on content type filter change ${contentTypeFilter.value}`)
  // Notify the child that data should be reloaded
  shouldReload.value = true
}

async function onSourceUrlFilterChange() {
  logger.debug(`on source URL filter change ${sourceUrlFilter.value}`)
  // Notify the child that data should be reloaded
  shouldReload.value = true
}

/**
 * Loads document data from the server with pagination and sorting support.
 * Fetches documents based on current page, items per page, and sort criteria, then updates the table display.
 */
async function loadItems() {
  loading.value = true

  try {
    const headers = {
      Accept: 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

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
    // Add document set filter if set
    if (documentSetFilter.value) {
      params.append('documentSetName', documentSetFilter.value)
    }
    // Add content type filter if set
    if (contentTypeFilter.value) {
      params.append('contentType', contentTypeFilter.value)
    }
    // Add source URL filter if set
    if (sourceUrlFilter.value) {
      params.append('sourceUrl', sourceUrlFilter.value)
    }

    const response = await fetch(`/api/documents/?${params}`, {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      throw new Error('Failed to get files')
    }

    const data = await response.json()

    return {
      totalItems: data.documentCount,
      items: data.documents.map((item) => toRaw(item)),
      tableUpdatedTime: data.tableUpdatedTime
    }
  } finally {
    loading.value = false
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
