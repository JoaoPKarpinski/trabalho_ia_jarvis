<script setup>
import { computed, onMounted, ref } from 'vue'
import NavigationSidebar from '../components/layout/NavigationSidebar.vue'
import ChatInterface from '../components/chat/ChatInterface.vue'
import AgendaViewer from '../components/agenda/AgendaViewer.vue'
import TaskManager from '../components/tasks/TaskManager.vue'
import QuizGenerator from '../components/quiz/QuizGenerator.vue'
import { useAgendaStore } from '../stores/agendaStore'
import { useTaskStore } from '../stores/taskStore'
import { useChatStore } from '../stores/chatStore'

const activePanel = ref('all')

const agendaStore = useAgendaStore()
const taskStore = useTaskStore()
const chatStore = useChatStore()

onMounted(() => {
  agendaStore.fetchAgenda()
  taskStore.fetchTasks()
})

const showChat = computed(() => activePanel.value === 'all' || activePanel.value === 'chat')
const showAgenda = computed(() => activePanel.value === 'all' || activePanel.value === 'agenda')
const showTasks = computed(() => activePanel.value === 'all' || activePanel.value === 'tasks')
const showQuiz = computed(() => activePanel.value === 'all' || activePanel.value === 'quiz')

const setPanel = (panel) => {
  activePanel.value = panel
}
</script>

<template>
  <div class="dashboard">
    <NavigationSidebar :active="activePanel" @select="setPanel" />

    <main class="dashboard-main">
      <section v-show="showChat" class="panel panel-chat">
        <header class="panel-header">
          <div>
            <p class="eyebrow">Assistente</p>
            <h2>Jarvis Academico</h2>
            <p class="subtitle">RAG, agenda e tarefas em um unico fluxo.</p>
          </div>
          <div class="status-chip" :class="{ loading: chatStore.isLoading }">
            {{ chatStore.isLoading ? 'Pensando' : 'Pronto' }}
          </div>
        </header>
        <ChatInterface />
      </section>

      <section v-show="showAgenda" class="panel panel-agenda">
        <header class="panel-header">
          <div>
            <p class="eyebrow">Agenda</p>
            <h2>Sua semana</h2>
            <p class="subtitle">Compromissos sincronizados do SQLite.</p>
          </div>
          <button class="ghost-button" @click="agendaStore.fetchAgenda()">Atualizar</button>
        </header>
        <AgendaViewer />
      </section>

      <section v-show="showTasks" class="panel panel-tasks">
        <header class="panel-header">
          <div>
            <p class="eyebrow">Tarefas</p>
            <h2>Foco diario</h2>
            <p class="subtitle">Organize e marque suas entregas.</p>
          </div>
          <button class="ghost-button" @click="taskStore.fetchTasks()">Recarregar</button>
        </header>
        <TaskManager />
      </section>

      <section v-show="showQuiz" class="panel panel-quiz">
        <header class="panel-header">
          <div>
            <p class="eyebrow">Exercicios</p>
            <h2>Geracao estatica</h2>
            <p class="subtitle">Crie quizzes estruturados a partir de um tema.</p>
          </div>
        </header>
        <QuizGenerator />
      </section>
    </main>
  </div>
</template>
