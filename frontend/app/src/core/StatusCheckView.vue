<template>
    <h2>Health Check</h2>
    <v-container>
        <v-col cols="auto">
            <v-card :color="statusColor" variant="elevated" class="mx-auto pa-2 ma-2">
                <div>
                    Status: {{ systemStatus }}
                </div>
            </v-card>
        </v-col>

        <v-col cols="auto">
            <v-btn class="ma-2" size="large" @click="onCheckStatus">Refresh</v-btn>
        </v-col>

    </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const systemStatus = ref('unknown')
const statusColor = ref('primary')

async function onCheckStatus() {
    systemStatus.value = 'unknown'
    await checkStatus()
}

onMounted(async () => { await checkStatus() })


async function checkStatus() {
    try {
        const response = await fetch('/api/status', {
            method: 'GET'
        });

        if (!response.ok) {
            systemStatus.value = 'offline'

            throw new Error('Status check failed');
        }

        const data = await response.json();
        console.log('Status check success:', data);

        if (data['status']) {
            systemStatus.value = data['status']
        }


    } catch (error) {
        console.error('Error during status check:', error);
    }
}

</script>

<style>
nav,
main {
    border: 2px solid #000;
    margin-bottom: 10px;
    padding: 10px;
}

nav>a+a {
    margin-left: 10px;
}

h2 {
    border-bottom: 1px solid #ccc;
    margin: 0 0 20px;
}
</style>