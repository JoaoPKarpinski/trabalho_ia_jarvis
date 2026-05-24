<script setup>
import { computed, ref } from 'vue'
import { useAgendaStore } from '../../stores/agendaStore'

const agendaStore = useAgendaStore()
const agendaItems = computed(() => agendaStore.items)
const selectedFile = ref(null)
const selectedName = ref('Nenhum arquivo')
const manualDate = ref('')
const manualTime = ref('')
const manualName = ref('')
const manualLocation = ref('')
const manualNotes = ref('')
const manualRows = ref([])

const handleChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    selectedName.value = file.name
  }
}

const uploadAgenda = async () => {
  await agendaStore.uploadAgenda(selectedFile.value)
  selectedFile.value = null
  selectedName.value = 'Nenhum arquivo'
}

const escapeCsv = (value) => {
  const text = String(value ?? '')
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

const addManualRow = () => {
  if (!manualDate.value || !manualTime.value || !manualName.value) return
  manualRows.value.push({
    date: manualDate.value,
    time: manualTime.value,
    name: manualName.value,
    location: manualLocation.value,
    notes: manualNotes.value
  })
  manualDate.value = ''
  manualTime.value = ''
  manualName.value = ''
  manualLocation.value = ''
  manualNotes.value = ''
}

const removeManualRow = (index) => {
  manualRows.value.splice(index, 1)
}

const sendManualCsv = async () => {
  if (manualRows.value.length === 0) return
  const header = ['Data', 'Hora', 'Nome', 'Local', 'Observações']
  const lines = manualRows.value.map((row) =>
    [row.date, row.time, row.name, row.location, row.notes].map(escapeCsv).join(',')
  )
  const csv = `${header.join(',')}\n${lines.join('\n')}`
  const file = new File([csv], 'agenda.csv', { type: 'text/csv' })
  await agendaStore.uploadAgenda(file)
  manualRows.value = []
}
</script>

<template>
  <div class="agenda">
    <div class="agenda-upload">
      <div>
        <p class="uploader-title">Agenda CSV</p>
        <p class="uploader-subtitle">{{ selectedName }}</p>
        <p class="agenda-help">
          Envie um CSV com cabecalho: Data, Hora, Nome, Local, Observações.
        </p>
      </div>
      <div class="uploader-actions">
        <label class="ghost-button">
          Selecionar
          <input class="uploader-input" type="file" accept=".csv" @change="handleChange" />
        </label>
        <button class="ghost-button" :disabled="!selectedFile" @click="uploadAgenda">Enviar</button>
      </div>
      <p class="uploader-status" :class="agendaStore.uploadStatus">
        {{ agendaStore.uploadMessage }}
      </p>
    </div>

    <div class="agenda-manual">
      <div>
        <p class="uploader-title">Entrada manual</p>
        <p class="uploader-subtitle">Preencha os campos e envie como CSV.</p>
      </div>
      <div class="agenda-manual-grid">
        <input v-model="manualDate" type="date" placeholder="Data" />
        <input v-model="manualTime" type="time" placeholder="Hora" />
        <input v-model="manualName" type="text" placeholder="Nome" />
        <input v-model="manualLocation" type="text" placeholder="Local" />
        <textarea v-model="manualNotes" rows="2" placeholder="Observações"></textarea>
      </div>
      <div class="agenda-manual-actions">
        <button class="ghost-button" @click="addManualRow">Adicionar linha</button>
        <button class="primary-button" :disabled="manualRows.length === 0" @click="sendManualCsv">
          Enviar CSV manual
        </button>
      </div>
      <div v-if="manualRows.length" class="agenda-manual-list">
        <div v-for="(row, index) in manualRows" :key="`${row.date}-${row.time}-${index}`" class="agenda-row">
          <div>
            <p class="agenda-title">{{ row.name }}</p>
            <p class="agenda-meta">
              {{ row.date }} • {{ row.time }} • {{ row.location || 'Sem local' }}
            </p>
            <p class="agenda-meta" v-if="row.notes">{{ row.notes }}</p>
          </div>
          <button class="ghost-button" @click="removeManualRow(index)">Remover</button>
        </div>
      </div>
    </div>

    <div v-if="agendaStore.isLoading" class="empty-state">Carregando agenda...</div>
    <div v-else-if="agendaItems.length === 0" class="empty-state">Sem compromissos ainda.</div>
    <ul v-else class="agenda-list">
      <li v-for="item in agendaItems" :key="item.id" class="agenda-item">
        <div>
          <p class="agenda-title">{{ item.title }}</p>
          <p class="agenda-meta" v-if="item.date || item.time">
            {{ item.date || 'Sem data' }} • {{ item.time || 'Sem horario' }}
          </p>
          <p class="agenda-meta" v-else>{{ item.raw }}</p>
        </div>
        <span class="agenda-tag">{{ item.date || 'Item' }}</span>
      </li>
    </ul>

    <p v-if="agendaStore.error" class="uploader-status error">
      {{ agendaStore.error }}
    </p>

    <pre v-if="agendaStore.text" class="agenda-text">{{ agendaStore.text }}</pre>
  </div>
</template>
