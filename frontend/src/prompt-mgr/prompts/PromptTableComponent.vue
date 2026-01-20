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
    :delete-single-item="deleteSinglePrompt"
    :delete-multiple-items="deleteMultiplePrompts"
    :load-items="loadItems"
    :load-table-stats="loadTableStats"
    :should-refresh="shouldRefresh"
  >
    <template #delete-dialog-text> Are you sure you want to delete this prompt? </template>

    <template #more-action-icons="{ item, index }">
      <v-icon class="me-2" size="small" @click="openEditDialog(item, index)">mdi-pencil</v-icon>
    </template>
    <template #more-action-dialogs>
      <edit-prompt-dialog
        v-model:active="activeConfirmEdit"
        v-model="targetItem"
        @confirmed="applyEditPrompt"
        @canceled="closeEditDialog"
      >
      </edit-prompt-dialog>
    </template>
  </common-data-table>
</template>

<script setup>
import { ref, toRaw } from 'vue'
import { storeToRefs } from 'pinia'
import CommonDataTable from '../../common/CommonDataTable.vue'
import { getAuthorization } from '../../common/AuthUtils.js'
import logger from '../../common/Logger.js'
import { usePromptStore } from './PromptStore'
import EditPromptDialog from './EditPromptDialog.vue'

const promptStore = usePromptStore()

const {
  page,
  itemsPerPage,
  totalItems,
  items,
  selectedItems,
  nameFilter,
  statusFilter,
  ownerTypeFilter
} = storeToRefs(promptStore)

const shouldRefresh = ref(false)

const headers = ref([
  {
    title: 'Name',
    value: 'name',
    sortable: true,
    filterable: true,
    filterModel: nameFilter
  },
  {
    title: 'Owner Type',
    value: 'ownerType',
    sortable: true,
    filterable: true,
    filterModel: ownerTypeFilter
  },
  { title: 'Actions', value: 'actions', sortable: false }
])

const sortBy = ref([])

const itemsPerPageOptions = [
  { value: 10, title: '10' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: 100, title: '100' }
]

const targetIndex = ref(-1)
const targetItem = ref({})

const activeFilterEdit = ref({})

const activeConfirmEdit = ref(false)

async function openEditDialog(item, index) {
  targetItem.value = { ...item }
  targetIndex.value = index
  activeConfirmEdit.value = true
}

async function closeEditDialog() {
  shouldRefresh.value = true

  targetItem.value = {}
  targetIndex.value = -1
  activeConfirmEdit.value = false
}

async function applyEditPrompt() {
  await editPrompt(targetItem.value)
  await closeEditDialog()
}

async function editPrompt(edittedPrompt) {
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const prompt_uuid = edittedPrompt.promptUuid
    const prompt_version_uuid = edittedPrompt.promptVersionUuid

    const response = await fetch(`/api/prompts/${prompt_uuid}/versions/${prompt_version_uuid}`, {
      method: 'PATCH',
      headers
    })

    if (!response.ok) {
      throw new Error(`Deleting prompt failed with status ${response.status}`)
    }

    await response.json()
    logger.apiSuccess('Prompt edit', { promptId: prompt_uuid })
  } catch (error) {
    console.error('Error editing:', error)
  }
}

async function deleteSinglePrompt(prompt) {
  const prompt_uuid = prompt.id
  try {
    const headers = {
      Accept: 'application/json',
      'Content-Type': 'application/json'
    }
    const auth = await getAuthorization()
    if (auth) {
      headers.Authorization = auth
    }

    const response = await fetch(`/api/prompts/${prompt_uuid}`, {
      method: 'DELETE',
      headers
    })

    if (!response.ok) {
      throw new Error(`Deleting prompt failed with status ${response.status}`)
    }

    await response.json()
    logger.apiSuccess('Prompt deleted', { promptId: prompt_uuid })
  } catch (error) {
    console.error('Error deleting:', error)
  }
}

async function deleteMultiplePrompts(prompts) {
  const promptUuids = prompts.map((x) => x.id)
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
      promptUuids
    }

    const response = await fetch('/api/prompts/delete', {
      method: 'POST',
      headers,
      body: JSON.stringify(body, null, 2)
    })

    if (!response.ok) {
      throw new Error(`Deleting prompts failed with status ${response.status}`)
    }

    await response.json()
    logger.apiSuccess('Selected prompts deleted', { count: body.promptUuids.length })
  } catch (error) {
    console.error('Error deleting:', error)
  }
}

async function loadTableStats() {
  const headers = {
    Accept: 'application/json'
  }
  const auth = await getAuthorization()
  if (auth) {
    headers.Authorization = auth
  } else {
    return {
      totalItems: 0,
      tableUpdatedTime: null
    }
  }

  const response = await fetch('/api/prompts/stats', {
    method: 'GET',
    headers
  })

  if (!response.ok) {
    throw new Error('Getting table stats failed')
  }

  const data = await response.json()

  return {
    totalItems: data.promptCount,
    tableUpdatedTime: data.tableUpdatedTime
  }
}

async function loadItems() {
  const headers = {
    Accept: 'application/json'
  }
  const auth = await getAuthorization()
  if (auth) {
    headers.Authorization = auth
  } else {
    return {
      totalItems: 0,
      items: [],
      tableUpdatedTime: null
    }
  }

  const params = new URLSearchParams({
    page: page.value - 1,
    itemsPerPage: itemsPerPage.value
  })

  if (sortBy.value.length > 0) {
    const sortByParam = sortBy.value
      .map((item) => (item.order === 'desc' ? `-${item.key}` : item.key))
      .join(',')

    params.append('sortBy', sortByParam)
  }

  if (nameFilter.value) {
    params.append('name', nameFilter.value)
  }
  if (statusFilter.value) {
    params.append('status', statusFilter.value)
  }
  if (ownerTypeFilter.value) {
    params.append('ownerType', ownerTypeFilter.value)
  }

  const response = await fetch(`/api/prompts/?${params}`, {
    method: 'GET',
    headers
  })

  if (!response.ok) {
    throw new Error('Failed to get prompts')
  }

  const data = await response.json()

  return {
    totalItems: data.promptCount,
    items: data.prompts.map((item) => toRaw(item)),
    tableUpdatedTime: data.tableUpdatedTime
  }
}
</script>

<style>
.action-icons {
  display: flex;
  gap: 4px;
  white-space: nowrap;
}
</style>
