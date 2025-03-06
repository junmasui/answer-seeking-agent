import { defineStore } from 'pinia'


export const useDocumentStore = defineStore('document', {
    state: () => {
        return {
            page: 1,
            itemsPerPage: 10,
            totalItems: 0,
            items: [],
            selectedItems: []
        }
    }
})
