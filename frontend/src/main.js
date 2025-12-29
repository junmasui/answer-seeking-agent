import './assets/main.css'
import 'vuetify/dist/vuetify.min.css'
import '@mdi/font/css/materialdesignicons.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import piniaPluginPersistedState from 'pinia-plugin-persistedstate'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Labs components require a manual import and installation of the component.
import { VDateInput } from 'vuetify/labs/VDateInput'
import { VFileUpload } from 'vuetify/labs/VFileUpload'
import { VNumberInput } from 'vuetify/labs/VNumberInput'
import { VTimePicker } from 'vuetify/labs/VTimePicker'
import { VTreeview } from 'vuetify/labs/VTreeview'

// Components
import router from './router'
import App from './App.vue'

const vuetify = createVuetify({
    icons: {
        iconfont: 'mdi'
    },
    components: {
        ...components,
        VDateInput,
        VFileUpload,
        VNumberInput,
        VTimePicker,
        VTreeview
    },
    directives,
    theme: {
        defaultTheme: 'dark'
    }
})

const pinia = createPinia()
pinia.use(piniaPluginPersistedState)

// Auth
import { authService } from './common/AuthService'

const app = createApp(App)
    .use(router)
    .use(pinia)
    .use(vuetify)


// Check for OIDC callback
if (window.location.search.includes('code=') && window.location.search.includes('state=')) {
    authService.handleCallback().then(() => {
        // Remove query params to clean URL
        window.history.replaceState({}, document.title, window.location.pathname)
        app.mount('#app')
    }).catch(err => {
        console.error("Auth Callback Error", err)
        app.mount('#app')
    })
} else {
    app.mount('#app')
}
