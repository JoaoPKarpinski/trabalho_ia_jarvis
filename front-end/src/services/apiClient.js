const baseUrl = 'http://localhost:8000/api'
const rootUrl = baseUrl.replace(/\/?api$/, '')

const normalizeError = async (response) => {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    const data = await response.json().catch(() => ({}))
    return data?.detail || data?.message || `Request failed with ${response.status}`
  }
  const text = await response.text().catch(() => '')
  return text || `Request failed with ${response.status}`
}

const request = async (path, options = {}) => {
  const url = `${baseUrl}${path}`
  const headers = options.headers ?? {}

  const response = await fetch(url, {
    ...options,
    headers
  })

  if (!response.ok) {
    const message = await normalizeError(response)
    throw new Error(message)
  }

  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json().catch(() => ({}))
  }

  return response.text().catch(() => '')
}

const withJson = (options = {}) => ({
  ...options,
  headers: {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  }
})

const get = (path) => request(path, withJson({ method: 'GET' }))
const post = (path, body) => request(path, withJson({ method: 'POST', body: JSON.stringify(body) }))
const put = (path, body) => request(path, withJson({ method: 'PUT', body: JSON.stringify(body) }))
const patch = (path, body) => request(path, withJson({ method: 'PATCH', body: JSON.stringify(body) }))
const upload = (path, formData) => request(path, { method: 'POST', body: formData })

const healthcheck = async () => {
  const response = await fetch(`${rootUrl}/health`, { method: 'GET' })

  if (!response.ok) {
    const message = await normalizeError(response)
    throw new Error(message)
  }

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json().catch(() => ({}))
  }

  return response.text().catch(() => '')
}

export { baseUrl, rootUrl, request, get, post, put, patch, upload, healthcheck }
export default { baseUrl, rootUrl, request, get, post, put, patch, upload, healthcheck }
