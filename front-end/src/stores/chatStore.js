import { defineStore } from 'pinia'
import apiClient from '../services/apiClient'

const nowIso = () => new Date().toISOString()

const createId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `msg-${Date.now()}-${Math.floor(Math.random() * 1000)}`
}

const buildHistory = (messages) =>
  messages
    .filter(
      (message) =>
        (message.role === 'user' || message.role === 'assistant') && !message.isError
    )
    .slice(-8)
    .map((message) => ({ role: message.role, content: message.content }))

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [
      {
        id: createId(),
        role: 'assistant',
        content: 'Pronto para ajudar no seu estudo.',
        timestamp: nowIso()
      }
    ],
    isLoading: false,
    uploadStatus: 'idle',
    uploadMessage: ''
  }),
  actions: {
    async sendMessage(text) {
      const content = text.trim()
      if (!content) return

      this.messages.push({
        id: createId(),
        role: 'user',
        content,
        timestamp: nowIso()
      })

      this.isLoading = true

      try {
        const history = buildHistory(this.messages.slice(0, -1))
        const data = await apiClient.post('/chat', { message: content, history })
        const reply = data?.reply || data?.message || 'Nenhuma resposta recebida.'
        this.messages.push({
          id: createId(),
          role: 'assistant',
          content: reply,
          timestamp: nowIso()
        })
      } catch (error) {
        this.messages.push({
          id: createId(),
          role: 'assistant',
          content: 'Erro ao conectar com o banco. Possivel indisponibilidade do servidor.',
          timestamp: nowIso(),
          isError: true
        })
      } finally {
        this.isLoading = false
      }
    },
    async uploadDocument(file) {
      if (!file) return

      this.uploadStatus = 'uploading'
      this.uploadMessage = 'Enviando arquivo...'

      try {
        const formData = new FormData()
        formData.append('file', file)
        const data = await apiClient.upload('/documents/upload', formData)
        const chunks = typeof data?.chunks_added === 'number' ? data.chunks_added : null
        this.uploadStatus = 'done'
        this.uploadMessage =
          data?.message ||
          (chunks === null ? 'Documento enviado para indexacao.' : `${chunks} chunks adicionados.`)
      } catch (error) {
        this.uploadStatus = 'error'
        this.uploadMessage = 'Falha no envio. Verifique o backend.'
      }
    }
  }
})
