import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import { emptyResume } from './resumeDefaults'
import AtsPanel from './components/AtsPanel'
import Preview from './components/Preview'
import ResumeForm from './components/ResumeForm'
import { buttonStyles, Card, Spinner, TextField } from './components/ui'

function Notice({ notice, onClose }) {
  const styles =
    notice.type === 'error'
      ? 'border-red-200 bg-red-50 text-red-800'
      : 'border-emerald-200 bg-emerald-50 text-emerald-800'
  return (
    <div role="status" className={`flex items-start justify-between gap-3 rounded-md border px-3 py-2 text-sm ${styles}`}>
      <span>{notice.text}</span>
      <button type="button" className="text-xs opacity-70 hover:opacity-100" onClick={onClose}>
        Close
      </button>
    </div>
  )
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export default function App() {
  const [resume, setResume] = useState(emptyResume)
  const [theme, setTheme] = useState('sidebar-green')
  const [themes, setThemes] = useState([])
  const [jd, setJd] = useState('')
  const [score, setScore] = useState(null)
  const [optimization, setOptimization] = useState(null)
  const [emailTo, setEmailTo] = useState('')
  const [busy, setBusy] = useState(null)
  const [notice, setNotice] = useState(null)
  const fileInput = useRef(null)

  useEffect(() => {
    api.themes().then(setThemes).catch((e) => setNotice({ type: 'error', text: e.message }))
    api
      .getResume()
      .then((stored) => {
        setResume({ ...emptyResume(), ...stored.resume })
        setTheme(stored.theme)
      })
      .catch((e) => e.status !== 404 && setNotice({ type: 'error', text: e.message }))
    api
      .lastJobDescription()
      .then((stored) => setJd(stored.jd_text))
      .catch(() => {})
  }, [])

  const run = async (action, fn) => {
    setBusy(action)
    setNotice(null)
    try {
      await fn()
    } catch (e) {
      setNotice({ type: 'error', text: e.message })
    } finally {
      setBusy(null)
    }
  }

  const handleImport = (file) =>
    run('import', async () => {
      setResume({ ...emptyResume(), ...(await api.parseResume(file)) })
      setScore(null)
      setOptimization(null)
      setNotice({ type: 'success', text: 'Resume imported. Review the fields, then save.' })
    })

  const handleSave = () =>
    run('save', async () => {
      await api.saveResume(resume, theme)
      setNotice({ type: 'success', text: 'Resume saved.' })
    })

  const handleScore = () =>
    run('score', async () => {
      setOptimization(null)
      setScore(await api.score(resume, jd))
    })

  const handleOptimize = () =>
    run('optimize', async () => {
      const result = await api.optimize(resume, jd)
      setScore(result.original_score)
      setOptimization(result)
    })

  const applyOptimized = () => {
    setResume(optimization.resume)
    setScore(optimization.final_score)
    setOptimization(null)
    setNotice({ type: 'success', text: 'Optimized resume applied. Save to keep it.' })
  }

  const handleDownload = () =>
    run('pdf', async () => {
      const name = resume.contact.name.trim().replace(/\W+/g, '_') || 'My'
      downloadBlob(await api.previewPdf(previewResume, theme), `${name}_Resume.pdf`)
    })

  const handleEmail = () =>
    run('email', async () => {
      const { sent_to } = await api.email(resume, theme, emailTo.trim())
      setNotice({ type: 'success', text: `Resume sent to ${sent_to}.` })
    })

  // While an optimized draft awaits Apply/Discard, the preview shows the draft.
  const previewResume = optimization?.optimized ? optimization.resume : resume

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-3 px-4 py-3">
          <h1 className="text-lg font-semibold text-slate-900">AI Resume Builder</h1>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <input
              ref={fileInput}
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                e.target.value = ''
                if (file) handleImport(file)
              }}
            />
            <button
              type="button"
              className={buttonStyles.secondary}
              disabled={Boolean(busy)}
              onClick={() => fileInput.current.click()}
            >
              {busy === 'import' && <Spinner />} Import PDF resume
            </button>
            <button type="button" className={buttonStyles.primary} disabled={Boolean(busy)} onClick={handleSave}>
              {busy === 'save' && <Spinner />} Save
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] space-y-4 px-4 py-4">
        {notice && <Notice notice={notice} onClose={() => setNotice(null)} />}
        {busy === 'import' && <p className="text-sm text-slate-500">Reading your resume with AI…</p>}

        <div className="grid gap-4 lg:grid-cols-2">
          <ResumeForm resume={resume} onChange={setResume} />

          <div className="space-y-4">
            <Preview
              resume={previewResume}
              theme={theme}
              themes={themes}
              onThemeChange={setTheme}
              onDownload={handleDownload}
              downloading={busy === 'pdf'}
              banner={
                optimization?.optimized && (
                  <p className="mb-2 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800 ring-1 ring-amber-200">
                    Showing the optimized draft. Apply or discard it in the ATS panel.
                  </p>
                )
              }
            />

            <AtsPanel
              jd={jd}
              onJdChange={setJd}
              score={score}
              optimization={optimization}
              busy={busy}
              onScore={handleScore}
              onOptimize={handleOptimize}
              onApply={applyOptimized}
              onDiscard={() => setOptimization(null)}
            />

            <Card title="Email">
              <div className="flex flex-wrap items-end gap-2">
                <div className="min-w-56 flex-1">
                  <TextField
                    label="Send to"
                    type="email"
                    value={emailTo}
                    onChange={setEmailTo}
                    placeholder="Leave empty to send to your GMAIL_ADDRESS"
                  />
                </div>
                <button type="button" className={buttonStyles.primary} disabled={Boolean(busy)} onClick={handleEmail}>
                  {busy === 'email' && <Spinner />} Email me the PDF
                </button>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  )
}
