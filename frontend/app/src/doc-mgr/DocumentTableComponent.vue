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
        <v-icon class="me-2" size="small" @click="ingestItem(item, index)">
          mdi-database-import
        </v-icon>
        <v-icon class="me-2" size="small" @click="editItem(item, index)"> mdi-pencil </v-icon>
        <v-icon size="small" @click="deleteItem(item, index)"> mdi-delete </v-icon>
      </div>
    </template>
  </v-data-table-server>
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
    v-model:active="activeConfirmDeleteItem"
    @done="closeDeleteItem"
    @confirmed="applyDeleteItem"
  >
    Are you sure you want to delete this item?
  </confirmation-dialog>
  <edit-doc-dialog v-model:active="activeEditDoc" @done="closeEditDoc" @confirmed="applyEditDoc">
  </edit-doc-dialog>

  <confirmation-dialog
    v-model:active="activeConfirmIngestSelected"
    @canceled="closeIngestSelected"
    @confirmed="applyIngestSelected"
  >
    Are you sure you want to ingest {{ selectedItemCount }} selected items?
  </confirmation-dialog>
  <confirmation-dialog
    v-model:active="activeConfirmDeleteSelected"
    @canceled="closeDeleteSelected"
    @confirmed="applyDeleteSelected"
  >
    Are you sure you want to delete {{ selectedItemCount }} selected items?
  </confirmation-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, toRaw } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import { useDocumentStore } from './DocStore'
import ConfirmationDialog from '../common/ConfirmationDialog.vue'
import logger from '../common/Logger.js'

const currentUserStore = useCurrentUserStore()
const documentStore = useDocumentStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)
const { page, itemsPerPage, totalItems, items, selectedItems } = storeToRefs(documentStore)
const tableUpdatedAt = ref()
const tableOutdated = ref(false)

const loading = ref(false)

const tableHeaders = ref([
  {
    title: 'File Name',
    value: 'name',
    width: '500px',
    sortable: true
  },
  { title: 'Size', key: 'sizeBytes', sortable: true },
  {
    title: 'Document Set',
    key: 'documentSetName',
    width: '150px',
    sortable: false
  },
  {
    title: 'Source URL',
    key: 'sourceUrl',
    width: '300px',
    sortable: false
  },
  {
    title: 'Content Type',
    key: 'contentType',
    width: '50px',
    sortable: false
  },
  { title: 'Status', key: 'status', width: '50px', sortable: true },
  {
    title: 'Ingestion Date',
    key: 'ingestionTime',
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
    key: 'downloadTimeUtc',
    width: '150px',
    sortable: true
  },
  { title: 'Actions', key: 'actions', width: '50px', sortable: false }
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

//
// Confirmation dialog for one-file ingestion
//

const activeConfirmIngestItem = ref(false)

function ingestItem(item, index) {
  activeConfirmIngestItem.value = true
  targetIndex.value = index
  targetItem.value = Object.assign({}, item)
}

async function applyIngestItem() {
  await ingestDocument(targetItem.value.id)
}

async function ingestDocument(doc_uuid) {
  try {
    const headers = {
      Accept: 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }
    const response = await fetch('/api/documents/ingest', {
      method: 'POST',
      headers
    })

    if (!response.ok) {
      throw new Error('Ingest failed')
    }

    const data = await response.json()
    logger.apiSuccess('Document ingest queued', { docId: doc_uuid })
  } catch (error) {
    console.error('Error ingesting:', error)
  }
}

async function closeIngestItem() {
  await loadItems()

  nextTick(() => {
    targetItem.value = {}
    targetIndex.value = -1
  })
}

//
// Edit document
//

const activeEditDoc = ref(false)

function editItem(item, index) {
  activeEditDoc.value = true
  targetIndex.value = index
  targetItem.value = Object.assign({}, item)
}

async function applyEditDoc() {
  await editDocument(targetItem.value.id)

  await closeEditDoc()
}

async function editDocument(doc_uuid) {}

async function closeEditDoc() {
  await loadItems()

  nextTick(() => {
    targetItem.value = {}
    targetIndex.value = -1
  })
}

//
// Confirmation dialog for one-file deletion
//

const activeConfirmDeleteItem = ref(false)

function deleteItem(item, index) {
  activeConfirmDeleteItem.value = true
  targetIndex.value = index
  targetItem.value = Object.assign({}, item)
}

async function applyDeleteItem() {
  await deleteDocument(targetItem.value.id)
}

async function deleteDocument(doc_uuid) {
  try {
    const headers = {
      Accept: 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const response = await fetch(`/api/documents/${doc_uuid}`, {
      method: 'DELETE',
      headers
    })

    if (!response.ok) {
      throw new Error('Delete failed')
    }

    const data = await response.json()
    logger.apiSuccess('Document deleted', { docId: doc_uuid })
  } catch (error) {
    console.error('Error deleting:', error)
  }
}

async function closeDeleteItem() {
  await loadItems()

  nextTick(() => {
    targetItem.value = {}
    targetIndex.value = -1
  })
}

//
// Confirmation dialog for ingestion of selected files
//

const activeConfirmIngestSelected = ref(false)

async function ingestSelectedItems() {
  activeConfirmIngestSelected.value = true
}

async function applyIngestSelected() {
  await ingestSelectedDocuments()
}

async function ingestSelectedDocuments() {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const body = {
      docUuids: selectedItems.value.map((x) => x.id)
    }

    const response = await fetch(`/api/documents/ingest`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error('Ingest failed')
    }

    // Clear the selections
    selectedItems.value = []

    const data = await response.json()
    logger.apiSuccess('Selected documents ingest queued', { count: body.docUuids.length })
  } catch (error) {
    console.error('Error ingesting:', error)
  }
}

async function closeIngestSelected() {
  await loadItems()
}

//
// Confirmation dialog for ingestion of all uploaded files
//

const activeConfirmIngestAllUploaded = ref(false)

async function ingestAllUploaded() {
  activeConfirmIngestAllUploaded.value = true
}

async function applyIngestAllUploaded() {
  await ingestAllUploadedDocuments()
}

async function ingestAllUploadedDocuments() {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const body = {
      allUploaded: true
    }

    const response = await fetch(`/api/documents/ingest`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error('Ingest failed')
    }

    const data = await response.json()
    logger.apiSuccess('All uploaded documents ingest queued')
  } catch (error) {
    console.error('Error ingesting:', error)
  }
}

async function closeIngestAllUploaded() {
  await loadItems()
}

//
// Confirmation dialog for deletion of selected files
//

const activeConfirmDeleteSelected = ref(false)

async function deleteSelectedItems() {
  activeConfirmDeleteSelected.value = true
}

async function applyDeleteSelected() {
  await deleteSelectedDocuments()
}

async function deleteSelectedDocuments() {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
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

    const data = await response.json()
    logger.apiSuccess('Selected documents deleted', { count: body.docUuids.length })
  } catch (error) {
    console.error('Error deleteing:', error)
  }
}

async function closeDeleteSelected() {
  await loadItems()
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

async function loadTableStats() {
  try {
    const headers = {
      Accept: 'application/json'
    }
    if (signedIn.value) {
      headers.Authorization = `Bearer ${accessToken.value}`
    }

    const response = await fetch('/api/documents/stats', {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      throw new Error('Getting table stats failed')
    }

    const data = await response.json()

    totalItems.value = data.documentCount
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

    const response = await fetch(`/api/documents/?${params}`, {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      throw new Error('Failed to get files')
    }

    const data = await response.json()

    totalItems.value = data.documentCount
    tableUpdatedAt.value = data.tableUpdatedTime
    tableOutdated.value = false
    items.value = data.documents.map((item) => toRaw(item))
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
