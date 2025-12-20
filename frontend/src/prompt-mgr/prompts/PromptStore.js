import { defineStore } from 'pinia'

export const usePromptStore = defineStore('prompt', {
  state: () => {
    return {
      page: 1,
      itemsPerPage: 10,
      totalItems: 0,
      items: [],
      selectedItems: [],
      nameFilter: '',
      statusFilter: '',
      ownerTypeFilter: ''
    }
  }
})
