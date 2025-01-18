<template>
    <v-dialog v-model="active" max-width="500px">
        <v-card class="pa-2 ma-2">
            <v-card-title class="text-h5">
                <v-form>
                    <!-- alternative icon was mdi-email-outline -->
                    <v-text-field variant="outlined" v-model="username" prepend-inner-icon="mdi-account-outline"
                        label="Enter your username"  density="compact"
                        placeholder="Enter your username"
                        ></v-text-field>
                    <v-text-field variant="outlined" v-model="password" prepend-inner-icon="mdi-lock-outline"
                        label="Enter your password" :append-inner-icon="passwordVisible ? 'mdi-eye-off' : 'mdi-eye'"
                        :type="passwordVisible ? 'text' : 'password'" density="compact"
                        placeholder="Enter your password" @click:append-inner="toggleVisibility"></v-text-field>
                </v-form>
            </v-card-title>
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
import { ref } from 'vue'

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

const username = ref('')
const passwordVisible = ref(false)
const password = ref('')

function toggleVisibility() {
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

        const response = await fetch(`/api/mock_auth/token`, {
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