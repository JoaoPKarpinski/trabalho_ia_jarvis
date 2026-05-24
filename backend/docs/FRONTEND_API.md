# Jarvis Backend - Swagger para Front-end

Este documento explica como usar o Swagger UI para testar os endpoints do backend e como o front-end deve consumir a API.

## Como abrir o Swagger UI

1. Instale as dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Inicie o servidor:

   ```bash
   uvicorn main:app --reload
   ```

3. Abra no navegador:

   - Swagger UI: http://localhost:8000/docs
   - Redoc: http://localhost:8000/redoc

## Base URL

- Local: http://localhost:8000
- Todos os endpoints da API usam o prefixo `/api`.

## Endpoints (resumo)

### Chat (LLM + Tools)

- **POST** `/api/chat`
  - Envia uma mensagem para o agente, com historico opcional.

**Request**

```json
{
  "message": "Explique regressao logistica",
  "history": [
    {"role": "user", "content": "Oi"},
    {"role": "assistant", "content": "Ola!"}
  ]
}
```

**Response**

```json
{
  "reply": "Resposta do agente..."
}
```

### Documentos (RAG)

- **POST** `/api/documents/upload`
  - Upload de arquivo PDF ou texto.
  - Usa `multipart/form-data` com campo `file`.

**Exemplo (curl)**

```bash
curl -F "file=@material.pdf" http://localhost:8000/api/documents/upload
```

**Response**

```json
{
  "chunks_added": 12
}
```

### Agenda (CSV)

- **POST** `/api/agenda/upload`
  - Upload do arquivo `agenda.csv` via `multipart/form-data`.

**Exemplo (curl)**

```bash
curl -F "file=@agenda.csv" http://localhost:8000/api/agenda/upload
```

**Response**

```json
{
  "status": "ok"
}
```

- **GET** `/api/agenda/text`
  - Retorna a agenda em texto pronto para a LLM.

**Response**

```json
{
  "text": "Agenda entries:\n1. date: 2026-05-21; time: 08:00; title: Aula"
}
```

### Tarefas

- **GET** `/api/tasks?include_completed=true`
  - Lista tarefas.

**Response**

```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Estudar embeddings",
      "description": "Capitulo 3",
      "due_date": "2026-05-25",
      "created_at": "2026-05-21T13:00:00+00:00",
      "completed": false
    }
  ]
}
```

- **POST** `/api/tasks`
  - Cria tarefa.

**Request**

```json
{
  "title": "Fazer exercicios",
  "description": "Lista 2",
  "due_date": "2026-05-23"
}
```

- **PATCH** `/api/tasks/{task_id}`
  - Atualiza tarefa.

**Request**

```json
{
  "title": "Fazer exercicios extras",
  "completed": true
}
```

- **PUT** `/api/tasks/{task_id}/complete`
  - Marca como concluida.

- **DELETE** `/api/tasks/{task_id}`
  - Remove tarefa.

### Healthcheck

- **GET** `/health`
  - Retorna status simples do servidor.

**Response**

```json
{
  "status": "ok"
}
```

## Observacoes

- Nao ha autenticacao no Swagger.
- O backend carrega `LLM_API_KEY` do arquivo `.env`.
- Para o front-end, o fluxo principal e usar `/api/chat` e as rotas de suporte (documentos, agenda, tarefas).
