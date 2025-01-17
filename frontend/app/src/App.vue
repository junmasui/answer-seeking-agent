<template>
  <v-app fluid>
    <v-app-bar>
      <v-app-bar-nav-icon icon="mdi-menu" variant="text" @click="toggleDrawer"></v-app-bar-nav-icon>

      <v-toolbar-title>All-in-One UI</v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn icon="mdi-theme-light-dark" @click="toggleTheme" variant="text"></v-btn>
      <v-tooltip max-width="300" text="Optional sign-in will enable long-memory personalization" location="bottom">
        <template v-slot:activator="{ props }">
          <v-btn :disabled="signedIn" v-bind="props" icon="mdi-login" @click="signIn" variant="text">
          </v-btn>
        </template>
      </v-tooltip>

      <v-btn icon="mdi-dots-vertical" id="overflow-button" variant="text">
      </v-btn>

      <v-menu activator="#overflow-button">
        <v-list>
          <v-list-item :disabled="!signedIn" @click="signOut">
            <template v-slot:prepend>
              <v-icon icon="mdi-logout"></v-icon>
            </template>
            <v-list-item-title>Sign Out</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

    </v-app-bar>
    <sign-in-dialog v-model:active="performSignIn" v-model:accessToken="accessToken" v-model:signedIn="signedIn" @onSuccess="signInSucceeded">
    </sign-in-dialog>

    <v-main>
      <v-container fluid class="pa=0 ma-0">
        <router-view />
      </v-container>
    </v-main>

    <v-navigation-drawer v-model:model-value="drawerModel" temporary>
      <v-list>
        <v-list-item title="Home" to="/"></v-list-item>
        <v-list-item title="About" to="/about"></v-list-item>
        <v-list-item title="Conversational" to="/conversational"></v-list-item>
        <v-list-item title="Document Manager" to="/doc-mgr"></v-list-item>
        <v-list-item title="Health" to="/health"></v-list-item>
      </v-list>
    </v-navigation-drawer>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import { useTheme } from 'vuetify'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from './CurrentUserStore.js'

import SignInDialog from './SignInDialog.vue'

const theme = useTheme()

const router = useRouter()

const drawerModel = ref(false)
const performSignIn = ref(false)

const currentUserStore = useCurrentUserStore();
const { signedIn, accessToken } = storeToRefs(currentUserStore)

function toggleDrawer() {
  drawerModel.value = !drawerModel.value;
}

function signIn() {
  performSignIn.value = true
}

function signInSucceeded() {
}

function signOut() {
  accessToken.value = ''
  signedIn.value = false
}

function toggleTheme() {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}

</script>

<style scoped></style>
