import { defineStore } from 'pinia'

export const useConversationStore = defineStore('upload', {
    state: () => {
        return {
            messages: [],
            userInput: '',
            threadId: ''
        }
    },
})
