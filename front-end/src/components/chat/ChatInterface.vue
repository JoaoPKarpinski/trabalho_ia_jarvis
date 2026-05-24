<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useChatStore } from '../../stores/chatStore'
import MessageBubble from './MessageBubble.vue'
import DocumentUploader from './DocumentUploader.vue'

const chatStore = useChatStore()
const input = ref('')
const historyRef = ref(null)

const isDisabled = computed(() => chatStore.isLoading)

const scrollToBottom = async () => {
  await nextTick()
  if (!historyRef.value) return
  historyRef.value.scrollTop = historyRef.value.scrollHeight
}

const sendMessage = async () => {
  const message = input.value.trim()
  if (!message) return
  await chatStore.sendMessage(message)
  input.value = ''
}

const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

watch(
  () => chatStore.messages.length,
  () => {
    scrollToBottom()
  },
  { flush: 'post' }
)

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="chat-interface">
    <div class="chat-history" ref="historyRef">
      <MessageBubble v-for="message in chatStore.messages" :key="message.id" :message="message" />
    </div>

    <div class="chat-tools">
      <DocumentUploader />

      <div class="composer">
        <textarea
          v-model="input"
          rows="3"
          placeholder="Digite sua pergunta..."
          @keydown="handleKeydown"
        ></textarea>
        <button class="primary-button" :disabled="isDisabled" @click="sendMessage">
          {{ isDisabled ? 'Enviando' : 'Enviar' }}
        </button>
      </div>
    </div>
  </div>
</template>
