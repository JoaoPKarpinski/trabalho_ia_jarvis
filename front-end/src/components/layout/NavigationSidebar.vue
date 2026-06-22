<script setup>
const props = defineProps({
  active: {
    type: String,
    default: 'all'
  }
})

const emit = defineEmits(['select'])

const options = [
  { id: 'all', label: 'Visao geral' },
  { id: 'chat', label: 'Chat' },
  { id: 'agenda', label: 'Agenda' },
  { id: 'tasks', label: 'Tarefas' },
  { id: 'quiz', label: 'Exercicios' },
  { id: 'study', label: 'Dissertativas' }
]
</script>

<template>
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark">J</div>
      <div>
        <p class="brand-kicker">Jarvis</p>
        <h1 class="brand-title">Academico</h1>
      </div>
    </div>

    <nav class="nav">
      <button
        v-for="item in options"
        :key="item.id"
        class="nav-button"
        :class="{ active: props.active === item.id }"
        @click="emit('select', item.id)"
      >
        {{ item.label }}
      </button>
    </nav>

  </aside>
</template>
