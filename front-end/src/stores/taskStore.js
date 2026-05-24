import { defineStore } from 'pinia'
import apiClient from '../services/apiClient'

export const useTaskStore = defineStore('tasks', {
  state: () => ({
    tasks: [],
    isLoading: false,
    error: null
  }),
  actions: {
    async fetchTasks() {
      this.isLoading = true
      this.error = null

      try {
        const data = await apiClient.get('/tasks?include_completed=true')
        this.tasks = Array.isArray(data?.tasks) ? data.tasks : []
      } catch (error) {
        this.tasks = []
        this.error = 'Erro ao conectar com o banco. Possivel indisponibilidade do servidor.'
      } finally {
        this.isLoading = false
      }
    },
    async addTask(payload) {
      const content = typeof payload === 'string' ? payload.trim() : payload?.title?.trim()
      if (!content) return

      const description = payload?.description?.trim() || ''
      const dueDate = payload?.due_date || null

      try {
        const data = await apiClient.post('/tasks', {
          title: content,
          description,
          due_date: dueDate
        })
        const newTask = data?.task || data
        if (newTask) {
          this.tasks.unshift(newTask)
          this.error = null
          return
        }
        this.error = 'Erro ao conectar com o banco. Possivel indisponibilidade do servidor.'
      } catch (error) {
        this.error = 'Erro ao conectar com o banco. Possivel indisponibilidade do servidor.'
      }
    },
    async toggleTask(task) {
      const previous = [...this.tasks]
      const updated = { ...task, completed: !task.completed }
      this.tasks = this.tasks.map((item) => (item.id === task.id ? updated : item))

      try {
        if (updated.completed) {
          await apiClient.request(`/tasks/${task.id}/complete`, { method: 'PUT' })
        } else {
          await apiClient.patch(`/tasks/${task.id}`, { completed: false })
        }
        this.error = null
      } catch (error) {
        this.tasks = previous
        this.error = 'Erro ao conectar com o banco. Possivel indisponibilidade do servidor.'
      }
    }
  }
})
