# Jarvis Academico - Front-end

Interface desktop do assistente Jarvis Academico (chat com RAG, agenda e tarefas), usando Vue 3 + Vite.

## Requisitos

- Node.js 20+ recomendado
- Backend rodando em `http://localhost:8000`

## Como rodar

```bash
npm install
npm run dev
```

## Integracao com o backend

- Base URL: `http://localhost:8000/api`
- Chat: `POST /api/chat`
- Documentos: `POST /api/documents/upload`
- Agenda: `POST /api/agenda/upload`, `GET /api/agenda/text`
- Tarefas: `GET /api/tasks?include_completed=true`, `POST /api/tasks`, `PATCH /api/tasks/{task_id}`, `PUT /api/tasks/{task_id}/complete`

O front-end usa o arquivo [src/services/apiClient.js](src/services/apiClient.js) para centralizar as chamadas.
