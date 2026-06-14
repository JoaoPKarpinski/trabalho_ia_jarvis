<script setup>
import { computed, ref } from 'vue'
import { useQuizStore } from '../../stores/quizStore'

const quizStore = useQuizStore()

const topic = ref('')
const numQuestions = ref(3)
const difficulty = ref('médio')
const selectedAnswers = ref({})

const difficultyOptions = ['fácil', 'médio', 'difícil']

const normalizedDifficulty = computed(() => {
  const value = String(difficulty.value || '').trim().toLowerCase()
  return difficultyOptions.includes(value) ? value : 'médio'
})

const getCorrectOptionIndex = (exercise) => {
  const value = Number.parseInt(exercise.indice_correto, 10)
  if (!Number.isFinite(value)) return -1
  return value > 0 ? value - 1 : value
}

const getSelectedOptionIndex = (exerciseIndex) => selectedAnswers.value[exerciseIndex] ?? null

const hasSelection = (exerciseIndex) => selectedAnswers.value[exerciseIndex] !== undefined

const selectOption = (exerciseIndex, optionIndex) => {
  selectedAnswers.value = {
    ...selectedAnswers.value,
    [exerciseIndex]: optionIndex
  }
}

const isCorrectSelection = (exerciseIndex, exercise, optionIndex) => {
  const selectedIndex = getSelectedOptionIndex(exerciseIndex)
  return selectedIndex !== null && selectedIndex === optionIndex && optionIndex === getCorrectOptionIndex(exercise)
}

const isIncorrectSelection = (exerciseIndex, exercise, optionIndex) => {
  const selectedIndex = getSelectedOptionIndex(exerciseIndex)
  return selectedIndex !== null && selectedIndex === optionIndex && optionIndex !== getCorrectOptionIndex(exercise)
}

const shouldShowCorrect = (exerciseIndex, exercise, optionIndex) => {
  const correctIndex = getCorrectOptionIndex(exercise)
  return hasSelection(exerciseIndex) && optionIndex === correctIndex
}

const generateQuiz = async () => {
  if (!difficultyOptions.includes(normalizedDifficulty.value)) {
    quizStore.error = 'Não foi possível gerar o quiz agora. Tente novamente.'
    return
  }

  selectedAnswers.value = {}

  await quizStore.generateQuiz({
    topic: topic.value,
    num_questions: numQuestions.value,
    difficulty: normalizedDifficulty.value
  })
}

</script>

<template>
  <div class="quiz-generator">
    <div class="quiz-form">
      <div class="quiz-field quiz-field-wide">
        <label for="quiz-topic">Tema opcional</label>
        <input
          id="quiz-topic"
          v-model="topic"
          type="text"
          placeholder="Ex.: regressão logística, embeddings, redes neurais"
        />
      </div>

      <div class="quiz-field">
        <label for="quiz-questions">Número de questões</label>
        <input id="quiz-questions" v-model="numQuestions" type="number" min="1" step="1" />
      </div>

      <div class="quiz-field">
        <label for="quiz-difficulty">Dificuldade</label>
        <select id="quiz-difficulty" v-model="difficulty">
          <option v-for="option in difficultyOptions" :key="option" :value="option">{{ option }}</option>
        </select>
      </div>

      <div class="quiz-field quiz-field-wide quiz-toggle">
        <button class="primary-button" :disabled="quizStore.isLoading" @click="generateQuiz">
          {{ quizStore.isLoading ? 'Gerando...' : 'Gerar Quiz' }}
        </button>
      </div>
    </div>

    <p v-if="quizStore.error" class="uploader-status error">{{ quizStore.error }}</p>

    <div v-if="quizStore.exercises.length" class="quiz-results">
      <article v-for="(exercise, exerciseIndex) in quizStore.exercises" :key="`${exerciseIndex}-${exercise.pergunta}`" class="quiz-card panel-like">
        <div class="quiz-card-header">
          <p class="quiz-card-index">Questão {{ exerciseIndex + 1 }}</p>
          <p v-if="exercise.referencia_fonte" class="quiz-source">{{ exercise.referencia_fonte }}</p>
        </div>

        <h3 class="quiz-question">{{ exercise.pergunta }}</h3>

        <div class="quiz-options">
          <button
            v-for="(option, optionIndex) in exercise.opcoes || []"
            :key="`${exerciseIndex}-${optionIndex}-${option}`"
            class="quiz-option"
            :class="{
              selected: getSelectedOptionIndex(exerciseIndex) === optionIndex,
              correct: shouldShowCorrect(exerciseIndex, exercise, optionIndex),
              incorrect: isIncorrectSelection(exerciseIndex, exercise, optionIndex),
              reveal: hasSelection(exerciseIndex)
            }"
            :disabled="hasSelection(exerciseIndex)"
            type="button"
            @click="selectOption(exerciseIndex, optionIndex)"
          >
            <span class="quiz-option-letter">{{ String.fromCharCode(65 + optionIndex) }}</span>
            <span class="quiz-option-text">{{ option }}</span>
          </button>
        </div>

        <div class="quiz-review" v-if="exercise.justificativa || exercise.referencia_fonte">
          <p v-if="exercise.justificativa"><strong>Justificativa:</strong> {{ exercise.justificativa }}</p>
          <p><strong>Fonte:</strong> {{ exercise.referencia_fonte || 'Não informada' }}</p>
        </div>
      </article>
    </div>
  </div>
</template>