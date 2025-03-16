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
            <v-icon class="me-2" size="small" @click="editItem(item, index)">
                mdi-pencil
            </v-icon>
            <v-icon size="small" @click="deleteItem(item, index)">
                mdi-delete
            </v-icon>

        </template>
    </v-data-table-server>
    <v-btn class="ma-2" size="large" @click="addDocSet">Add New</v-btn>
    <v-btn class="ma-2" size="large" @click="loadItems">Refresh</v-btn>
    <add-doc-set-dialog v-model:active="activeAddDocSet" v-model="targetItem" @done="closeAddDocSet" @confirmed="applyAddDocSet">
    </add-doc-set-dialog>
    <edit-doc-set-dialog v-model:active="activeEditDocSet" v-model="targetItem" @done="closeEditDocSet" @confirmed="applyEditDocSet">
    </edit-doc-set-dialog>
    <confirmation-dialog v-model:active="activeConfirmDelete" @done="closeDeleteItem" @confirmed="applyDeleteItem">
        Are you sure you want to delete this item?
    </confirmation-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, toRaw } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../common/CurrentUserStore'
import { useDocumentSetStore } from './DocSetStore';
import ConfirmationDialog from '../common/ConfirmationDialog.vue';
import AddDocSetDialog from './AddDocSetDialog.vue';
import EditDocSetDialog from './EditDocSetDialog.vue';

const currentUserStore = useCurrentUserStore();
const documentSetStore = useDocumentSetStore()

const { signedIn, accessToken } = storeToRefs(currentUserStore)
const { page, itemsPerPage, totalItems, items, selectedItems } = storeToRefs(documentSetStore);
const tableUpdatedAt = ref();
const tableOutdated = ref(false);

const loading = ref(false);

const headers = ref([
    {
        title: 'Document Set',
        key: 'name',
        width: '150px'
    },
    { title: 'Is Public', value: 'isPublicViewable' },
    { title: 'Is Default', key: 'isNewDocDefault' },
    {
        title: 'Last Modified Date',
        key: 'modificationTime'
    },
    { title: 'Status', key: 'status' },
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
// Add new document-set dialog
//
const activeAddDocSet = ref(false)

function addDocSet() {
    activeAddDocSet.value = true

    targetIndex.value = -1
    targetItem.value = {

        name: '',
        isPublicViewable: true,
        isNewDocDefault: false

    }
}


async function applyAddDocSet() {
    await addDocumentSet()
}

async function addDocumentSet() {

    try {

        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const body = {
            name: targetItem.value.name,
            isNewDocDefault: targetItem.value.isNewDocDefault,
            isPublicViewable: targetItem.value.isPublicViewable,
        }

        const response = await fetch(`/api/document-sets/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body, null, 2)
        });

        if (!response.ok) {
            throw new Error('Add failed');
        }

        const data = await response.json();
        console.log('Added successfully:', data);
    } catch (error) {
        console.error('Error adding:', error);
    }

}


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

function editItem(item, index) {
    activeEditDocSet.value = true
    targetIndex.value = index
    targetItem.value = Object.assign({}, item)

    console.log('EditItem:', JSON.stringify(targetItem.value, null, 2));


}

async function applyEditDocSet() {
    await editDocumentSet(targetItem.value.id)
}

async function editDocumentSet(doc_set_uuid) {
    try {

        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const body = {
            // name: targetItem.value.name,
            isNewDocDefault: targetItem.value.isNewDocDefault,
            isPublicViewable: targetItem.value.isPublicViewable,
        }

        console.log('Edited:', body);
        console.log('Edited:', JSON.stringify(body, null, 2));


        const response = await fetch(`/api/document-sets/${doc_set_uuid}`, {
            method: 'PATCH',
            headers: headers,
            body: JSON.stringify(body, null, 2)
        });

        if (!response.ok) {
            throw new Error('Edit failed');
        }

        const data = await response.json();
        console.log('Edited successfully:', data);
    } catch (error) {
        console.error('Error editing:', error);
    }
}


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

function deleteItem(item, index) {
    activeConfirmDelete.value = true
    targetIndex.value = index
    targetItem.value = Object.assign({}, item)
}

async function applyDeleteItem() {
    await deleteDocumentSet(targetItem.value.id)
}

async function deleteDocumentSet(doc_set_uuid) {
    try {

        const headers = {
            'Accept': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const response = await fetch(`/api/document-sets/${doc_set_uuid}`, {
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


async function closeDeleteItem() {
    await loadItems()

    nextTick(() => {
        targetItem.value = {}
        targetIndex.value = -1
    })
}

//
// Dialog for single document set change
//

const pickDocumentSet = ref(false)
const selectedDocumentSet = ref({})

function changeDocumentSet(item, index) {
    pickDocumentSet.value = true
    targetIndex.value = index
    targetItem.value = Object.assign({}, item)

    selectedDocumentSet.value = documentSets.value.find(x => x.id === item.documentSetId)
}

async function selectNewDocSet() {
    await updateDocSet(targetItem.value.id, selectedDocumentSet.value.id)

    await closePickDocSet()
}

async function updateDocSet(doc_uuid, doc_set_uuid) {
    try {

        const headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if (signedIn.value) {
            headers['Authorization'] = `Bearer ${accessToken.value}`
        }

        const body = {
            documentSetId: doc_set_uuid
        }

        const response = await fetch(`/api/documents/${doc_uuid}`, {
            method: 'PATCH',
            headers: headers,
            body: JSON.stringify(body, null, 2)
        });

        if (!response.ok) {
            throw new Error('Update failed');
        }

        const data = await response.json();
        console.log('Update successfully:', data);
    } catch (error) {
        console.error('Error updating document set:', error);
    }
}

async function closePickDocSet() {
    await loadItems()

    nextTick(() => {
        targetItem.value = {}
        targetIndex.value = -1
    })
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

        const response = await fetch(`/api/document-sets/stats`, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Getting table stats failed');
        }

        const data = await response.json();

        totalItems.value = data.documentSetCount;
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

        const response = await fetch(`/api/document-sets/?${params}`, {
            method: 'GET',
            headers: headers
        });

        if (!response.ok) {
            throw new Error('Failed to get files');
        }

        const data = await response.json();

        totalItems.value = data.documentSetCount;
        tableUpdatedAt.value = data.tableUpdatedTime
        tableOutdated.value = false
        items.value = data.documentSets.map(item => toRaw(item));

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