import { defineStore } from 'pinia'
import apiClient from '../services/apiClient'

const allowedDifficulties = ['fácil', 'médio', 'difícil']

const normalizeDifficulty = (difficulty) => {
  const value = String(difficulty || '').trim().toLowerCase()
  if (allowedDifficulties.includes(value)) {
    return value
  }
  return 'médio'
}

export const useQuizStore = defineStore('quiz', {
  state: () => ({
    exercises: [],
    isLoading: false,
    error: '',
    lastRequest: null
  }),
  actions: {
    async generateQuiz({ topic = null, num_questions = 3, difficulty = 'médio' } = {}) {
      const safeDifficulty = normalizeDifficulty(difficulty)
      const amount = Number.parseInt(num_questions, 10)
      const safeAmount = Number.isFinite(amount) && amount > 0 ? amount : 3
      const normalizedTopic = typeof topic === 'string' ? topic.trim() : ''

      this.isLoading = true
      this.error = ''

      try {
        const response = await apiClient.post('/quiz/generate', {
          topic: normalizedTopic || null,
          num_questions: safeAmount,
          difficulty: safeDifficulty
        })

        const exercises = Array.isArray(response?.exercicios) ? response.exercicios : []
        this.exercises = exercises
        this.lastRequest = {
          topic: normalizedTopic || null,
          num_questions: safeAmount,
          difficulty: safeDifficulty
        }

        if (exercises.length === 0) {
          this.error = 'Não foi possível gerar o quiz agora. Tente novamente.'
        }
      } catch (error) {
        this.exercises = []
        this.error = 'Não foi possível gerar o quiz agora. Tente novamente.'
      } finally {
        this.isLoading = false
      }
    }
  }
})