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
    VFileUpload
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

const app = createApp(App).use(router).use(pinia).use(vuetify)

// Check for OIDC callback
if (window.location.search.includes('code=') && window.location.search.includes('state=')) {
  authService
    .handleCallback()
    .then((user) => {
      // Remove query params to clean URL
      window.history.replaceState({}, document.title, window.location.pathname)
      app.mount('#app')

      // Redirect to original path if present in state
      if (user && user.state && user.state.returnPath) {
        router.push(user.state.returnPath)
      }
    })
    .catch((err) => {
      console.error('Auth Callback Error', err)
      app.mount('#app')
    })
} else {
  app.mount('#app')
}
