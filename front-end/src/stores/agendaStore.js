import { defineStore } from 'pinia'
import apiClient from '../services/apiClient'

const parseAgendaText = (text) => {
  if (!text) return []

  return text
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.toLowerCase().startsWith('agenda entries'))
    .map((line, index) => {
      const cleaned = line.replace(/^\d+\.\s*/, '')
      const parts = cleaned.split(';').map((part) => part.trim())
      const item = { id: `agenda-${index}`, raw: cleaned }

      parts.forEach((part) => {
        const [key, ...rest] = part.split(':')
        if (!rest.length) return
        const value = rest.join(':').trim()
        const normalized = key.trim().toLowerCase()

        if (normalized === 'date') item.date = value
        if (normalized === 'time') item.time = value
        if (normalized === 'title') item.title = value
      })

      if (!item.title) {
        item.title = cleaned
      }

      return item
    })
}

export const useAgendaStore = defineStore('agenda', {
  state: () => ({
    text: '',
    items: [],
    isLoading: false,
    error: null,
    lastSync: null,
    uploadStatus: 'idle',
    uploadMessage: ''
  }),
  actions: {
    async fetchAgenda() {
      this.isLoading = true
      this.error = null

      try {
        const data = await apiClient.get('/agenda/text')
        this.text = data?.text || ''
        this.items = parseAgendaText(this.text)
        this.lastSync = new Date().toISOString()
      } catch (error) {
        this.text = ''
        this.items = []
        this.error = 'Erro ao conectar com o banco. Possivel indisponibilidade do servidor.'
      } finally {
        this.isLoading = false
      }
    },
    async uploadAgenda(file) {
      if (!file) return

      this.uploadStatus = 'uploading'
      this.uploadMessage = 'Enviando agenda...'

      try {
        const formData = new FormData()
        formData.append('file', file)
        await apiClient.upload('/agenda/upload', formData)
        this.uploadStatus = 'done'
        this.uploadMessage = 'Agenda enviada com sucesso.'
        await this.fetchAgenda()
      } catch (error) {
        this.uploadStatus = 'error'
        this.uploadMessage = 'Falha no envio da agenda.'
      }
    }
  }
})
