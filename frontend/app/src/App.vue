<template>
  <v-app fluid>
    <v-app-bar>
      <v-app-bar-nav-icon icon="mdi-menu" variant="text" @click="toggleDrawer"></v-app-bar-nav-icon>

      <v-toolbar-title>All-in-One UI</v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn icon="mdi-theme-light-dark" variant="text" @click="toggleTheme"></v-btn>
      <v-tooltip
        max-width="300"
        text="Optional sign-in will enable long-memory personalization"
        location="bottom"
      >
        <template #activator="{ props }">
          <v-btn
            :disabled="signedIn"
            v-bind="props"
            icon="mdi-login"
            variant="text"
            @click="signIn"
          >
          </v-btn>
        </template>
      </v-tooltip>

      <v-btn id="overflow-button" icon="mdi-dots-vertical" variant="text"> </v-btn>

      <v-menu activator="#overflow-button">
        <v-list>
          <v-list-item :disabled="!signedIn" @click="signOut">
            <template #prepend>
              <v-icon icon="mdi-logout"></v-icon>
            </template>
            <v-list-item-title>Sign Out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>
    <sign-in-dialog
      v-model:active="performSignIn"
      v-model:accessToken="accessToken"
      v-model:refreshToken="refreshToken"
      v-model:refreshAccessAfter="refreshAccessAfter"
      v-model:signed-in="signedIn"
      @on-success="signInSucceeded"
    >
    </sign-in-dialog>

    <v-main>
      <v-container fluid class="pa=0 ma-0">
        <router-view />
      </v-container>
    </v-main>

    <v-navigation-drawer v-model:model-value="drawerModel" temporary>
      <v-list>
        <v-list-item title="Home" to="/"></v-list-item>
        <!-- Reinsert when we have meaningful info:
          <v-list-item title="About" to="/about"></v-list-item>
        -->
        <v-list-item title="Status" to="/status"></v-list-item>
        <v-list-item title="Document Manager" to="/doc-mgr"></v-list-item>
        <v-list-item title="Conversational" to="/conversational"></v-list-item>
        <v-list-item title="Administrator" to="/admin"></v-list-item>
      </v-list>
    </v-navigation-drawer>
  </v-app>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTheme } from 'vuetify'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from './common/CurrentUserStore.js'

import SignInDialog from './common/SignInDialog.vue'

const theme = useTheme()

const router = useRouter()
const route = useRoute()

const drawerModel = ref(false)
const performSignIn = ref(false)

const currentUserStore = useCurrentUserStore()
const { signedIn, accessToken, refreshToken, refreshAccessAfter } = storeToRefs(currentUserStore)

/**
 * Toggles the visibility of the navigation drawer.
 * Opens or closes the side navigation menu for mobile and desktop navigation.
 */
function toggleDrawer() {
  drawerModel.value = !drawerModel.value
}

/**
 * Opens the sign-in dialog for user authentication.
 * Displays the authentication modal for users to enter their credentials.
 */
function signIn() {
  performSignIn.value = true
}

/**
 * Handles successful sign-in completion.
 * Called after the user successfully authenticates through the sign-in dialog.
 */
function signInSucceeded() {
  // If user was trying to access a protected route, redirect there
  // Otherwise, redirect to conversational page

  console.log(`ACCESS ${accessToken.value}`)
  console.log(`REFRESH ${refreshToken.value}`)
  console.log(`REFRESH ${refreshAccessAfter.value}`)

  const returnTo = route.query.returnTo || '/conversational'
  router.push(returnTo)
}

// Watch for route changes to handle protected routes
watch(
  () => route.path,
  (newPath) => {
    // Redirect to sign-in if accessing admin without authentication
    if (newPath === '/admin' && !signedIn.value) {
      router.push(`/?returnTo=${encodeURIComponent(newPath)}`)
      performSignIn.value = true
    }
  }
)

/**
 * Signs out the current user by clearing authentication data.
 * Resets the access token and signed-in status to log out the user.
 */
function signOut() {
  accessToken.value = ''
  refreshToken.value = ''
  refreshAccessAfter.value = null
  signedIn.value = false
  // Redirect to home page after sign-out
  router.push('/')
}

/**
 * Toggles between light and dark themes.
 * Switches the Vuetify theme between light and dark modes based on current setting.
 */
function toggleTheme() {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}
</script>

<!-- Scoped styles - ensures CSS rules only apply to this component, preventing style conflicts -->
<style scoped></style>
