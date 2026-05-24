<script setup>
const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['toggle'])

const toggleTask = () => {
  emit('toggle', props.task)
}
</script>

<template>
  <div class="task-item" :class="{ done: props.task.completed }">
    <label class="task-check">
      <input type="checkbox" :checked="props.task.completed" @change="toggleTask" />
      <span class="checkmark"></span>
    </label>
    <div class="task-info">
      <p class="task-title">{{ props.task.title }}</p>
      <p class="task-meta">
        {{ props.task.description || 'Sem detalhes' }}
        <span v-if="props.task.due_date">• {{ props.task.due_date }}</span>
      </p>
    </div>
  </div>
</template>
