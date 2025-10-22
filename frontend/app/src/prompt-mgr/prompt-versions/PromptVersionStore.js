import { defineStore } from 'pinia'

export const usePromptVersionStore = defineStore('prompt-version', {
  state: () => {
    return {
      page: 1,
      itemsPerPage: 10,
      totalItems: 0,
      items: [],
      selectedItems: [],
      nameFilter: '',
      statusFilter: ''
    }
  }
})
