<script setup>
import { computed, ref } from 'vue'
import { useTaskStore } from '../../stores/taskStore'
import TaskItem from './TaskItem.vue'

const taskStore = useTaskStore()
const titleInput = ref('')
const descriptionInput = ref('')
const dueDateInput = ref('')

const remaining = computed(() => taskStore.tasks.filter((task) => !task.completed).length)

const addTask = async () => {
  const title = titleInput.value.trim()
  if (!title) return
  await taskStore.addTask({
    title,
    description: descriptionInput.value.trim(),
    due_date: dueDateInput.value || null
  })
  titleInput.value = ''
  descriptionInput.value = ''
  dueDateInput.value = ''
}
</script>

<template>
  <div class="tasks">
    <div class="task-input">
      <input
        v-model="titleInput"
        type="text"
        placeholder="Nova tarefa"
        @keydown.enter.prevent="addTask"
      />
      <input v-model="descriptionInput" type="text" placeholder="Descricao (opcional)" />
      <input v-model="dueDateInput" type="date" />
      <button class="primary-button" @click="addTask">Adicionar</button>
    </div>
    <p class="task-summary">{{ remaining }} pendentes</p>
    <p v-if="taskStore.error" class="uploader-status error">{{ taskStore.error }}</p>
    <div class="task-list">
      <TaskItem v-for="task in taskStore.tasks" :key="task.id" :task="task" @toggle="taskStore.toggleTask" />
    </div>
  </div>
</template>
