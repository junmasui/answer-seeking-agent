<template>
  <h2>Conversational View</h2>


  <div class="d-flex justify-end">
    <v-btn @click="onClearConversation" class="pa-2 ma-2" variant="tonal">
      Clear Conversation
    </v-btn>
  </div>

  <v-container fluid>
    <v-container fluid v-for="(item, index) in messages" :key="index" class="pa-0 ma-0">
      <v-row class="pa-0 ma-0">
        <v-col v-if="item.type === 'user'" cols="12" class="pa-0 ma-0">
          <UserMessageComponent :message="item.message" />
        </v-col>
        <v-col v-else-if="item.type === 'system'" cols="12" class="pa-0 ma-0">
          <SystemMessageComponent :message="item.message" />
        </v-col>
      </v-row>

    </v-container>

    <!--- Regarding `@keydown.enter`:
      `.exact` means that the event listens for exactly ENTER, and SHIFT+ENTER will not be captured.
      This allows extra lines to be created with SHIFT+ENTER
      `.prevent' instructs the browser to ignore the event, which will keep a spurious newline from
      being appended.
     -->
    <v-textarea label="Query" clearable counter persistent-clear persistent-counter v-model="userInput"
      :disabled="querySubmitted"
      @click:clear="onClear" @keydown.enter.exact.prevent="submit()"></v-textarea>

    <v-container>
      <v-row class="flex-nowrap" no-gutters>
        <v-col cols="4"> </v-col>
        <v-col cols="4" class="justify-center max-width: 200px">
          <v-progress-linear :active="querySubmitted" :indeterminate="true" color="primary"></v-progress-linear>
        </v-col>
        <v-col cols="4"> </v-col>
      </v-row>
    </v-container>

  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { storeToRefs } from 'pinia'

import { useCurrentUserStore } from '../CurrentUserStore'
import { useConversationStore } from './ConversationStore'

import SystemMessageComponent from './SystemMessageComponent.vue'
import UserMessageComponent from './UserMessageComponent.vue'

const currentUserStore = useCurrentUserStore();
const conversationStore = useConversationStore();

const { signedIn, accessToken } = storeToRefs(currentUserStore)
const { userInput, messages, threadId } = storeToRefs(conversationStore);

const querySubmitted = ref(false)


function onClearConversation(event) {
  messages.value = []
  userInput.value = ''
  threadId.value = ''
}

function onClear(event) {
  userInput.value = ''
}

async function submit(event) {
  try {

    const queryParams = new URLSearchParams();
    queryParams.append('q', userInput.value);
    // Nuance about false-y: null, undefined and zero-length strings are falsey
    if (threadId.value) {
      queryParams.append('threadId', threadId.value);
    }

    //threadId on queryParams

    querySubmitted.value = true

    const headers = {
          'Accept': 'application/json'
    }
    if ( signedIn.value ) {
      headers['Authorization'] = `Bearer ${accessToken.value}`
    }

    const response = await fetch('/api/answer?' + queryParams.toString(),
      {
        method: 'GET', // GET is the default, so you could omit this line
        headers: headers
      }
    );

    querySubmitted.value = false


    if (!response.ok) {
      throw new Error('Query failed');
    }

    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      console.log(`Response content type: ${contentType}`)
      throw new TypeError("Oops, we haven't got JSON!");
    }

    const data = await response.json();

    messages.value.push({ type: 'user', message: userInput.value })
    userInput.value = ''

    threadId.value = data?.threadId ?? ''

    messages.value.push({ type: 'system', message: data?.answer ?? '' })

  } catch (error) {
    console.error('Error: query failed', error);
  }


}


</script>

<style module>
h2 {
  border-bottom: 1px solid #ccc;
  margin: 0 0 20px;
}
</style>