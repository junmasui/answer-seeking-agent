<template>
  <v-dialog v-model="active" max-width="500px">
    <v-card class="pa-2 ma-2">
      <v-card-title class="text-h5"> Sign In </v-card-title>
      <v-card-text>
        <v-alert
          v-model="alertVisible"
          closable
          title="Simulated authentication in use"
          type="info"
          variant="tonal"
          class="mb-2"
        >
          <ul>
            <li>
              Do not expose to beyond local system before replacing with a real OAuth2 service.
            </li>
            <li>Email/username and password are not validated.</li>
            <li>Password field must have minimum 3 characters.</li>
          </ul>
        </v-alert>

        <v-form>
          <!-- alternative prepend-inner-icon was mdi-email-outline -->
          <v-text-field
            v-model="username"
            variant="outlined"
            prepend-inner-icon="mdi-account-outline"
            label="Enter your email or username"
            density="compact"
            placeholder="Enter your email or username"
          ></v-text-field>
          <v-text-field
            v-model="password"
            variant="outlined"
            prepend-inner-icon="mdi-lock-outline"
            label="Enter your password"
            :append-inner-icon="passwordVisible ? 'mdi-eye-off' : 'mdi-eye'"
            :type="passwordVisible ? 'text' : 'password'"
            density="compact"
            placeholder="Enter your password"
            @click:append-inner="togglePasswordVisibility"
          ></v-text-field>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="text" @click="onCancel">Cancel</v-btn>
        <v-btn color="primary" variant="text" @click="onConfirm">OK</v-btn>
        <v-spacer></v-spacer>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ACCESS_TOKEN_EXPIRY_BUFFER_SECONDS } from './AppConstants'

const active = defineModel('active', {
  type: Boolean,
  default: false
})
const signedIn = defineModel('signedIn', {
  type: Boolean,
  default: false
})
const accessToken = defineModel('accessToken', {
  type: String,
  default: ''
})
const refreshToken = defineModel('refreshToken', {
  type: String,
  default: ''
})
const refreshAccessAfter = defineModel('refreshAccessAfter', {
  type: Date,
  default: null
})

const emit = defineEmits(['onSuccess', 'onFail'])

const alertVisible = ref(true)

const username = ref('')
const passwordVisible = ref(false)
const password = ref('')

let alertTimeoutId // Updated from var

watch(alertVisible, (newValue, _oldValue) => {
  // Clear any existing timeout
  clearTimeout(alertTimeoutId)
  alertTimeoutId = 0
  if (newValue === false) {
    // Set a timeout to make the alert visible after 5 minutes
    alertTimeoutId = setTimeout(() => {
      alertVisible.value = true // Reset the value
    }, 300000) // 5 minutes in milliseconds
  }
})

/**
 * Toggles the visibility of the password field between text and password input types.
 * Allows users to show or hide their password while typing for better usability.
 */
function togglePasswordVisibility() {
  passwordVisible.value = !passwordVisible.value
}

/**
 * Handles the cancel action by closing the sign-in dialog.
 * Allows users to dismiss the dialog without attempting authentication.
 */
function onCancel() {
  active.value = false
}

/**
 * Handles the sign-in confirmation by attempting authentication with the provided credentials.
 * Sends credentials to the simulated auth endpoint and updates the signed-in state on success.
 */
async function onConfirm() {
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const response = await fetch('/api/sim_auth/token', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error('Sign in failed')
    }

    const data = await response.json()

    console.log(`DATA ${JSON.stringify(data, null, 2)}`)

    signedIn.value = true

    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    const now = new Date()
    // 30-second safety window
    refreshAccessAfter.value = new Date(
      now.getTime() + (data.expires_in - ACCESS_TOKEN_EXPIRY_BUFFER_SECONDS) * 1000
    )

    console.log(`ACCESS ${accessToken.value}`)
    console.log(`REFRESH ${refreshToken.value}`)
    console.log(`REFRESH ${refreshAccessAfter.value}`)

    emit('onSuccess')
  } catch (error) {
    console.error('Could not sign in:', error)
    emit('onFail', error)
  }

  active.value = false
}
</script>
