<template>
    <v-banner class="pa-2 ma-2" icon="mdi-alert-circle" color="warning" lines="one" v-if="tableOutdated">
        <v-banner-text>
            Newer table data is available.
        </v-banner-text>

        <template v-slot:actions>
            <v-btn variant="text" @click="loadItems">Refresh</v-btn>
        </template>
    </v-banner>
    <v-data-table-server show-select return-object v-model="selectedItems" v-model:page="page"
        v-model:items-per-page="itemsPerPage" :items-per-page-options="itemsPerPageOptions" :items-length="totalItems"
        :headers="headers" :items="items" density="compact" item-key="name" @update:options="loadItems">
        <template v-slot:item.actions="{ item, index }">
            <v-icon class="me-2" size="small" @click="ingestItem(item, index)">
                mdi-database-import
            </v-icon>
            <v-icon size="small" @click="deleteItem(item, index)">
                mdi-delete
            </v-icon>
            <confirmation-dialog v-model:active="confirmIngest" @canceled="closeIngest" @confirmed="ingestItemConfirm">
                Are you sure you want to ingest this item?
            </confirmation-dialog>
            <confirmation-dialog v-model:active="confirmIngestSelected" @canceled="closeIngestSelected"
                @confirmed="ingestSelectedConfirm">
                Are you sure you want to ingest {{ selectedItemCount }} selected items?
            </confirmation-dialog>
            <confirmation-dialog v-model:active="confirmDelete" @canceled="closeDelete" @confirmed="deleteItemConfirm">
                Are you sure you want to delete this item?
            </confirmation-dialog>

        </template>
    </v-data-table-server>
    <v-btn class="ma-2" size="large" @click="ingestSelectedItems" :disabled="selectedItemCount === 0">Ingest
        Selected</v-btn>
    <v-btn class="ma-2" size="large" @click="loadItems">Refresh</v-btn>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import { useDocumentStore } from './DocStore';
import ConfirmationDialog from '../common/ConfirmationDialog.vue';

const currentUserStore = useCurrentUserStore();
const documentStore = useDocumentStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)
const { page, itemsPerPage, totalItems, items, selectedItems } = storeToRefs(documentStore);
const tableUpdatedAt = ref();
const tableOutdated = ref(false);

const loading = ref(false);

const headers = ref([
    { title: 'File Name', value: 'name' },
    { title: 'Size', key: 'sizeBytes' },
    {
        title: 'Last Modified Date',
        key: 'modificationTime'
    },
    { title: 'Status', key: 'status' },
    {
        title: 'Ingestion Date',
        key: 'ingestionTime'
    },
    { title: 'Actions', key: 'actions', sortable: false },
])

const itemsPerPageOptions = ([
    { value: 2, title: '2' },
    { value: 5, title: '5' },
    { value: 10, title: '10' },
    { value: 25, title: '25' },
    { value: 50, title: '50' }
]
)

const selectedItemCount = computed(() => {
    return selectedItems.value.length;
})

const targetIndex = ref(-1)
const targetItem = ref({})

//
// Confirmation dialog for one-file ingestion
//

const confirmIngest = ref(false)

function ingestItem(item, index) {
    confirmIngest.value = true
    targetIndex.value = index
    targetItem.value = Object.assign({}, item)
}

async function ingestItemConfirm() {
    await ingestDocument(targetItem.value.id)

    await closeIngest()
}

async function ingestDocument(doc_uuid) {
    try {

        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }
        const response = await fetch(`/api/documents/${doc_uuid}/ingest`, {
            method: 'POST',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Ingest failed');
        }

        const data = await response.json();
        console.log('Ingest queued successfully:', data);
    } catch (error) {
        console.error('Error ingesting:', error);
    }
}


async function closeIngest() {
    await loadItems()

    nextTick(() => {
        targetItem.value = {}
        targetIndex.value = -1
    })
}

//
// Confirmation dialog for one-file deletion
//

const confirmDelete = ref(false)

function deleteItem(item, index) {
    confirmDelete.value = true
    targetIndex.value = index
    targetItem.value = Object.assign({}, item)
}

async function deleteItemConfirm() {
    await deleteDocument(targetItem.value.id)

    await closeDelete()
}

async function deleteDocument(doc_uuid) {
    try {

        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const response = await fetch(`/api/documents/${doc_uuid}`, {
            method: 'DELETE',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Delete failed');
        }

        const data = await response.json();
        console.log('Deleted successfully:', data);
    } catch (error) {
        console.error('Error deleting:', error);
    }
}


async function closeDelete() {
    await loadItems()

    nextTick(() => {
        targetItem.value = {}
        targetIndex.value = -1
    })
}

//
// Confirmation dialog for ingestion of selected files
//

const confirmIngestSelected = ref(false)

async function ingestSelectedItems() {
    confirmIngestSelected.value = true

}

async function ingestSelectedConfirm() {
    await ingestSelectedDocuments()

    await closeIngestSelected()
}

async function ingestSelectedDocuments() {
    try {

        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const body = {
            docUuids: selectedItems.value.map(x => x.id)
        }

        const response = await fetch(`/api/documents/ingest`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body, null, 2)
        });

        if (!response.ok) {
            throw new Error('Ingest failed');
        }

        const data = await response.json();
        console.log('Ingest queued successfully:', data);
    } catch (error) {
        console.error('Error ingesting:', error);
    }
}


async function closeIngestSelected() {
    await loadItems()
}


//
// Polling for server table updates.
//

var intervalId = null;

onMounted(async () => {
    await loadItems();

    intervalId = setInterval(async () => {
        await loadTableStats()
    },
        30000)
})

onBeforeUnmount(async () => {
    clearInterval(intervalId);
    intervalId = null;
})

async function loadTableStats() {
    try {

        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const response = await fetch(`/api/documents/stats`, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Getting table stats failed');
        }

        const data = await response.json();

        totalItems.value = data.documentCount;
        if (tableUpdatedAt.value !== data.tableUpdatedTime) {
            tableOutdated.value = true;
            tableUpdatedAt.value = data.tableUpdatedTime;
        }
    } catch (error) {
        console.error('Error getting table stats:', error);
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

        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const response = await fetch(`/api/documents/?${params}`, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Failed to get files');
        }

        const data = await response.json();

        totalItems.value = data.documentCount;
        tableUpdatedAt.value = data.tableUpdatedTime
        tableOutdated.value = false
        items.value = data.documents;

    } catch (error) {
        totalItems.value = 0;
        tableOutdated.value = false
        items.value = [];
        loading.value = false
        console.error('Error getting files:', error);
    }
    loading.value = false
}


</script>

<style></style>