<template>
    <v-dialog v-model="active" max-width="500px">
        <v-card class="pa-2 ma-2">
            <v-card-title class="text-h5">
                Sign In
            </v-card-title>
            <v-card-text>
                <v-alert closable title="Simulated authentication in use"
                    text="Do not expose to beyond local system before replacing witha real OAuth2 service. Email/username and password are not being validated."
                    type="info" variant="tonal" v-model="alertVisible" class="mb-2"></v-alert>


                <v-form>
                    <!-- alternative prepend-inner-icon was mdi-email-outline -->
                    <v-text-field variant="outlined" v-model="username" prepend-inner-icon="mdi-account-outline"
                        label="Enter your email or username" density="compact"
                        placeholder="Enter your email or username"></v-text-field>
                    <v-text-field variant="outlined" v-model="password" prepend-inner-icon="mdi-lock-outline"
                        label="Enter your password" :append-inner-icon="passwordVisible ? 'mdi-eye-off' : 'mdi-eye'"
                        :type="passwordVisible ? 'text' : 'password'" density="compact"
                        placeholder="Enter your password" @click:append-inner="togglePasswordVisibility"></v-text-field>
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

const active = defineModel('active', {
    type: Boolean,
    default: false
});
const signedIn = defineModel('signedIn', {
    type: Boolean,
    default: false
});
const accessToken = defineModel('acccessToken', {
    type: String,
    default: ''
});

const emit = defineEmits(['onSuccess'])

const alertVisible = ref(true)

const username = ref('')
const passwordVisible = ref(false)
const password = ref('')


var alertTimeoutId;

watch(alertVisible, (newValue, oldValue) => {
    // Clear any existing timeout
    clearTimeout(alertTimeoutId);
    alertTimeoutId = 0;
    if (newValue === false) {
        // Set a timeout to make the alert visible after 5 minutes
        alertTimeoutId = setTimeout(() => {
            alertVisible.value = true; // Reset the value
        }, 300000); // 5 minutes in milliseconds
    }
});

function togglePasswordVisibility() {
    passwordVisible.value = !passwordVisible.value
}

async function onCancel() {
    active.value = false
}

async function onConfirm() {
    try {

        const formData = new FormData();
        formData.append('username', username.value);
        formData.append('password', password.value);

        const response = await fetch(`/api/sim_auth/token`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Sign in failed');
        }

        const data = await response.json();

        signedIn.value = true
        accessToken.value = data['access_token']

    } catch (error) {
        console.error('Could not sign in:', error);
    }

    active.value = false

    emit('onSuccess')
}

</script>
<style></style>