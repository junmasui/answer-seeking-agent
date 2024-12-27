import { defineStore } from 'pinia'

export const useUploadStore = defineStore('upload', {
    state: () => {
        return {
            fileList: []
        }
    }
})
