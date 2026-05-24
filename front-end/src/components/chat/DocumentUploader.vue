<script setup>
import { ref } from 'vue'
import { useChatStore } from '../../stores/chatStore'

const chatStore = useChatStore()
const selectedFile = ref(null)
const selectedName = ref('Nenhum arquivo')

const handleChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    selectedName.value = file.name
  }
}

const uploadFile = async () => {
  await chatStore.uploadDocument(selectedFile.value)
  selectedFile.value = null
  selectedName.value = 'Nenhum arquivo'
}
</script>

<template>
  <div class="uploader">
    <div class="uploader-info">
      <p class="uploader-title">Documentos</p>
      <p class="uploader-subtitle">{{ selectedName }}</p>
    </div>
    <div class="uploader-actions">
      <label class="ghost-button">
        Escolher
        <input class="uploader-input" type="file" accept=".pdf,.txt" @change="handleChange" />
      </label>
      <button class="ghost-button" :disabled="!selectedFile" @click="uploadFile">Enviar</button>
    </div>
    <p class="uploader-status" :class="chatStore.uploadStatus">
      {{ chatStore.uploadMessage }}
    </p>
  </div>
</template>
