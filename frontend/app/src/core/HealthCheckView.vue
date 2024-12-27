<template>
    <h2>Health Check</h2>
    <v-container>
        <v-col cols="auto">
            <v-card :color="statusColor" variant="elevated" class="mx-auto pa-2 ma-2">
                <div>
                    Status: {{ healthStatus }}
                </div>
            </v-card>
        </v-col>

        <v-col cols="auto">
            <v-btn class="ma-2" size="large" @click="onCheckHealth">Refresh</v-btn>
        </v-col>

    </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const healthStatus = ref('unknown')
const statusColor = ref('indigo')

async function onCheckHealth() {
    healthStatus.value = 'unknown'
    await checkHealth()
}

onMounted(async () => { await checkHealth() })


async function checkHealth() {
    try {
        const response = await fetch('/api/health', {
            method: 'GET'
        });

        if (!response.ok) {
            healthStatus.value = 'unhealthy'

            throw new Error('Health check failed');
        }

        const data = await response.json();
        console.log('Health check success:', data);

        if (data['status'] === 'healthy') {
            healthStatus.value = 'healthy'
        }


    } catch (error) {
        console.error('Error during health check:', error);
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