<template>
  <v-container class="fill-height justify-center" fluid>
    <v-card class="elevation-12 rounded-lg" max-width="500" width="100%">
      <v-card-text class="text-center pa-8">
        <v-icon
          icon="mdi-shield-lock-outline"
          size="64"
          color="primary"
          class="mb-6"
        ></v-icon>
        
        <h2 class="text-h4 font-weight-bold mb-4 text-primary">Authentication Required</h2>
        
        <p class="text-body-1 text-medium-emphasis mb-8">
          Access to this resource is protected. Please log in with your credentials to continue.
        </p>

        <v-alert
          v-if="errorMessage"
          type="error"
          variant="tonal"
          class="mb-6 text-left"
          closable
        >
          {{ errorMessage }}
        </v-alert>

        <v-btn
          color="primary"
          size="x-large"
          block
          rounded="lg"
          elevation="4"
          prepend-icon="mdi-login"
          :loading="loading"
          @click="handleLogin"
        >
          Log In
        </v-btn>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { authService } from '../common/AuthService'
import logger from '../common/Logger'

const loading = ref(false)
const errorMessage = ref('')
const route = useRoute()

// Capture the redirect path from query parameters
const returnPath = ref('/')

onMounted(() => {
  if (route.query.redirect) {
    returnPath.value = route.query.redirect
  }
})

async function handleLogin() {
  loading.value = true
  errorMessage.value = ''
  
  try {
    // Pass the return path to the sign in method
    await authService.signIn(returnPath.value)
  } catch (error) {
    logger.error('Login initiation failed', error)
    errorMessage.value = 'Failed to initialize login. Please try again.'
    loading.value = false
  }
}
</script>
