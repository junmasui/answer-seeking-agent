import { defineStore } from 'pinia'


export const useCurrentUserStore = defineStore('currentUser', {
    state: () => {
        return {
            signedIn: false,
            username: '',
            accessToken: ''
        }
    },
    persist: true,
})
