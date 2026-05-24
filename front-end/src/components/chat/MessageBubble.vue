<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

marked.setOptions({ breaks: true })

const isUser = computed(() => props.message.role === 'user')
const rendered = computed(() => {
  const content = props.message.content || ''
  return DOMPurify.sanitize(marked.parse(content))
})
</script>

<template>
  <div class="bubble" :class="{ 'bubble-user': isUser, 'bubble-error': props.message.isError }">
    <div class="bubble-meta">
      <span class="bubble-role">{{ isUser ? 'Voce' : 'Jarvis' }}</span>
      <span v-if="props.message.timestamp" class="bubble-time">
        {{ new Date(props.message.timestamp).toLocaleTimeString() }}
      </span>
    </div>
    <div class="bubble-content" v-html="rendered"></div>
  </div>
</template>
