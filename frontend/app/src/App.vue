<template>
  <v-app fluid>
    <v-app-bar>
      <v-app-bar-nav-icon icon="mdi-menu" variant="text" @click="toggleDrawer"></v-app-bar-nav-icon>

      <v-toolbar-title>All-in-One UI</v-toolbar-title>

      <v-spacer></v-spacer>

      <v-btn icon="mdi-theme-light-dark" @click="toggleTheme" variant="text"></v-btn>
      <v-btn icon="mdi-dots-vertical" variant="text"></v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="pa=0 ma-0">
        <router-view/>
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

const theme = useTheme()

const drawerModel = ref(false)

function toggleDrawer() {
  drawerModel.value = !drawerModel.value;
}

function toggleTheme() {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}

</script>

<style scoped>
</style>
