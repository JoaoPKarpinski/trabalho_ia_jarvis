<script setup>
import { nextTick, ref } from 'vue'
import apiClient from '../../services/apiClient'

const initialAssistantMessage = {
  id: 'intro-1',
  role: 'assistant',
  content:
    'Vamos trabalhar com active recall. Primeiro, envie um tema. A partir dele, vou buscar materiais relacionados e começar a fazer perguntas, avaliando suas respostas ao longo da sessão. Quando quiser finalizar, use "Encerrar Sessão" para receber a síntese do desempenho.'
}

const createMessageId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `study-${Date.now()}-${Math.floor(Math.random() * 1000)}`
}

const messages = ref([initialAssistantMessage])
const sessionId = ref(null)
const currentTopic = ref('')
const inputText = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const sessionComplete = ref(false)
const historyRef = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (!historyRef.value) return
  historyRef.value.scrollTop = historyRef.value.scrollHeight
}

const resetSession = async () => {
  messages.value = [initialAssistantMessage]
  sessionId.value = null
  currentTopic.value = ''
  inputText.value = ''
  isLoading.value = false
  errorMessage.value = ''
  sessionComplete.value = false
  await scrollToBottom()
}

const normalizeResponseText = (payload) => {
  return payload?.jarvis_message || ''
}

const sendMessage = async (message) => {
  const content = String(message || '').trim()
  if (!content || isLoading.value || sessionComplete.value) return

  errorMessage.value = ''

  messages.value.push({
    id: createMessageId(),
    role: 'user',
    content
  })

  isLoading.value = true

  try {
    const response = await apiClient.post('/study/session/message', {
      session_id: sessionId.value,
      message: content
    })

    const assistantMessage = normalizeResponseText(response)
    const returnedSessionId = response?.session_id ?? response?.sessionId ?? null
    const returnedTopic = response?.topic ?? currentTopic.value

    if (assistantMessage) {
      messages.value.push({
        id: createMessageId(),
        role: 'assistant',
        content: assistantMessage
      })
    } else {
      throw new Error('Resposta vazia do servidor.')
    }

    sessionId.value = returnedSessionId
    currentTopic.value = returnedTopic || currentTopic.value

    if (
      content.toLowerCase() === 'encerrar sessão' ||
      content.toLowerCase() === 'encerrar sessao' ||
      String(response?.status || '').toLowerCase().includes('encerr')
    ) {
      sessionComplete.value = true
    }

    await scrollToBottom()
  } catch (error) {
    errorMessage.value = 'Não foi possível enviar a mensagem agora. Tente novamente.'
  } finally {
    isLoading.value = false
  }
}

const submitMessage = async () => {
  const content = inputText.value.trim()
  if (!content) return
  inputText.value = ''
  await sendMessage(content)
}

const finishSession = async () => {
  if (isLoading.value) return
  inputText.value = ''
  await sendMessage('encerrar sessão')
}
</script>

<template>
  <div class="study-session">
    <div class="study-session-meta">
      <p class="study-session-label">Session ID</p>
      <p class="study-session-value">{{ sessionId || 'null' }}</p>
      <p v-if="currentTopic" class="study-session-topic">Tema atual: {{ currentTopic }}</p>
    </div>

    <div ref="historyRef" class="study-history">
      <article
        v-for="message in messages"
        :key="message.id"
        class="study-message"
        :class="message.role === 'user' ? 'study-message-user' : 'study-message-assistant'"
      >
        <div class="study-message-badge">{{ message.role === 'user' ? 'Você' : 'Jarvis' }}</div>
        <p class="study-message-content">{{ message.content }}</p>
      </article>
    </div>

    <div class="study-actions">
      <textarea
        v-model="inputText"
        class="study-input"
        rows="3"
        placeholder="Digite o tema ou sua resposta..."
        :disabled="sessionComplete || isLoading"
        @keydown.enter.exact.prevent="submitMessage"
        @keydown.enter.shift.exact.stop
      ></textarea>

      <div class="study-action-row">
        <button class="primary-button" :disabled="sessionComplete || isLoading" @click="submitMessage">
          {{ isLoading ? 'Enviando...' : 'Enviar' }}
        </button>
        <button class="ghost-button" :disabled="isLoading || sessionComplete" @click="finishSession">
          Encerrar Sessão
        </button>
      </div>

      <p v-if="errorMessage" class="uploader-status error">{{ errorMessage }}</p>

      <div v-if="sessionComplete" class="study-finish-box">
        <p class="study-finish-title">Sessão encerrada.</p>
        <p class="study-finish-text">Você pode limpar a tela e iniciar uma nova sessão.</p>
        <button class="primary-button" @click="resetSession">Nova Sessão</button>
      </div>
    </div>
  </div>
</template>