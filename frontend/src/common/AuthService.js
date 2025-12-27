import { UserManager, WebStorageStateStore } from 'oidc-client-ts'

// These should be configurable via environment variables in a real app
// For now we hardcode for the known dev setup, effectively generic standard defaults.
const OIDC_SETTINGS = {
    authority: 'http://localhost:28080/realms/tenant-1',
    client_id: 'api-client',
    redirect_uri: window.location.origin,
    post_logout_redirect_uri: window.location.origin,
    response_type: 'code',
    scope: 'openid profile email doc:read doc:write doc:ingest prompt:read prompt:write query',
    userStore: new WebStorageStateStore({ store: window.localStorage }),
    automaticSilentRenew: true,
}

class AuthService {
    constructor() {
        this.userManager = new UserManager(OIDC_SETTINGS)

        this.userManager.events.addUserLoaded((user) => {
            console.log('User loaded', user)
        })

        this.userManager.events.addAccessTokenExpiring(() => {
            console.log('Token expiring...')
        })

        this.userManager.events.addAccessTokenExpired(() => {
            console.log('Token expired')
        })

        this.userManager.events.addUserSignedOut(() => {
            console.log('User signed out')
        })
    }

    async getUser() {
        return this.userManager.getUser()
    }

    async signIn() {
        return this.userManager.signinRedirect()
    }

    async signOut() {
        return this.userManager.signoutRedirect()
    }

    async handleCallback() {
        return this.userManager.signinRedirectCallback()
    }
}

export const authService = new AuthService()
