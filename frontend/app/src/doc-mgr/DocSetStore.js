import { defineStore } from 'pinia'


export const useDocumentSetStore = defineStore('documentSet', {
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
