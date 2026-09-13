const BASE = '/api'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, raw = false } = {}) {
  const init = { method, headers: {} }
  if (body instanceof FormData) {
    init.body = body
  } else if (body !== undefined) {
    init.body = JSON.stringify(body)
    init.headers['Content-Type'] = 'application/json'
  }

  let res
  try {
    res = await fetch(BASE + path, init)
  } catch {
    throw new ApiError('Cannot reach the server. Is the backend running?', 0)
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const data = await res.json()
      message = data?.error?.message || (typeof data?.detail === 'string' ? data.detail : message)
    } catch {
      // Non-JSON error body (e.g. a proxy timeout page): keep the generic message.
    }
    throw new ApiError(message, res.status)
  }
  return raw ? res : res.json()
}

const post = (path, body, opts) => request(path, { method: 'POST', body, ...opts })

export const api = {
  themes: () => request('/themes'),
  getResume: () => request('/resume'),
  lastJobDescription: () => request('/job-description'),
  saveResume: (resume, theme) => post('/resume', { resume, theme }),
  parseResume: (file) => {
    const form = new FormData()
    form.append('file', file)
    return post('/resume/parse', form)
  },
  previewHtml: async (resume, theme) =>
    (await post('/resume/preview', { resume, theme, format: 'html' }, { raw: true })).text(),
  previewPdf: async (resume, theme) =>
    (await post('/resume/preview', { resume, theme, format: 'pdf' }, { raw: true })).blob(),
  score: (resume, jobDescription) => post('/ats/score', { resume, job_description: jobDescription }),
  optimize: (resume, jobDescription) => post('/ats/optimize', { resume, job_description: jobDescription }),
  email: (resume, theme, to) => post('/resume/email', { resume, theme, to: to || null }),
}
