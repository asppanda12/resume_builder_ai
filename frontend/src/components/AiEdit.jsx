import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { buttonStyles, Spinner } from './ui'

// Flattens a section into readable lines so a before/after pair can be compared line by line.
function flatten(value, key = '') {
  if (typeof value === 'string') {
    const text = value.trim()
    if (!text) return []
    if (key === 'bullets') return [`• ${text}`]
    return [key && key !== 'items' ? `${key}: ${text}` : text]
  }
  if (Array.isArray(value)) return value.flatMap((item) => flatten(item, key))
  if (value && typeof value === 'object') return Object.entries(value).flatMap(([k, v]) => flatten(v, k))
  return []
}

function diff(before, after) {
  const removed = flatten(before)
  const added = []
  for (const line of flatten(after)) {
    const i = removed.indexOf(line)
    if (i === -1) added.push(line)
    else removed.splice(i, 1)
  }
  return { removed, added }
}

function SparkleIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" className="h-3.5 w-3.5">
      <path d="M10 1.5l1.9 5.1 5.1 1.9-5.1 1.9L10 15.5l-1.9-5.1L3 8.5l5.1-1.9L10 1.5zM16 13l.8 2.2L19 16l-2.2.8L16 19l-.8-2.2L13 16l2.2-.8L16 13z" />
    </svg>
  )
}

function DiffView({ changes }) {
  if (!changes.removed.length && !changes.added.length) {
    return <p className="mt-1.5 text-slate-500">The AI returned the section unchanged.</p>
  }
  return (
    <ul className="mt-1.5 space-y-0.5">
      {changes.removed.map((line, i) => (
        <li key={`r${i}`} className="rounded bg-red-50 px-1.5 py-0.5 text-red-800 line-through decoration-red-300">
          − {line}
        </li>
      ))}
      {changes.added.map((line, i) => (
        <li key={`a${i}`} className="rounded bg-emerald-50 px-1.5 py-0.5 text-emerald-800">
          + {line}
        </li>
      ))}
    </ul>
  )
}

/**
 * AI-edit control for one section. Each instance owns its own state, so several sections can be
 * mid-edit at once. Render prop: children({ button, panel }) places the trigger and the panel.
 * onReplace(target, next) must swap `target` for `next` in the latest resume state.
 */
export function AiEditable({ sectionName, label, data, onReplace, children }) {
  const [open, setOpen] = useState(false)
  const [instruction, setInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [applied, setApplied] = useState(null) // { before, after, instruction }
  const [showDiff, setShowDiff] = useState(true)
  const latest = useRef(data)

  useEffect(() => {
    latest.current = data
  }, [data])

  const isEmpty = flatten(data).length === 0

  const submit = async () => {
    const text = instruction.trim()
    if (!text || loading) return
    const before = data
    setLoading(true)
    setError(null)
    try {
      const { section_data: after } = await api.editSection(sectionName, before, text)
      // Never overwrite edits the user made while the request was running.
      if (latest.current !== before) {
        setError('This section changed while the AI was working, so the edit was not applied. Try again.')
        return
      }
      onReplace(before, after)
      setApplied({ before, after, instruction: text })
      setShowDiff(true)
      setOpen(false)
      setInstruction('')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const undo = () => {
    if (latest.current !== applied.after) {
      setError('This section was edited after the AI change, so it can no longer be undone.')
    } else {
      onReplace(applied.after, applied.before)
    }
    setApplied(null)
  }

  const button = (
    <button
      type="button"
      onClick={() => {
        setOpen((o) => !o)
        setError(null)
      }}
      disabled={isEmpty && !open}
      title={isEmpty ? 'Add some content first' : `Edit ${label} with AI`}
      aria-label={`Edit ${label} with AI`}
      aria-expanded={open}
      className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-xs font-medium text-violet-700 hover:bg-violet-50 disabled:cursor-not-allowed disabled:opacity-40"
    >
      {loading ? <Spinner /> : <SparkleIcon />} AI edit
    </button>
  )

  const panel = (open || error || applied) && (
    <div className="mb-3 space-y-2">
      {open && (
        <div className="rounded-md border border-violet-200 bg-violet-50 p-2">
          <textarea
            autoFocus
            rows={2}
            value={instruction}
            disabled={loading}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit()
              if (e.key === 'Escape') setOpen(false)
            }}
            maxLength={500}
            placeholder='What should change? e.g. "make this punchier", "shorten to 2 bullets", "fix grammar only"'
            className="w-full rounded-md border border-violet-200 bg-white px-2.5 py-1.5 text-sm shadow-sm placeholder:text-slate-400 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500"
          />
          <div className="mt-1.5 flex items-center justify-between gap-2">
            <span className="text-xs text-slate-500">
              {loading ? 'Editing this section…' : 'Only this section is sent. ⌘/Ctrl+Enter to apply.'}
            </span>
            <div className="flex items-center gap-2">
              <button type="button" className="text-xs text-slate-500 hover:text-slate-700" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                className={`${buttonStyles.primary} bg-violet-700 px-2.5 py-1 text-xs hover:bg-violet-800`}
                disabled={!instruction.trim() || loading}
                onClick={submit}
              >
                {loading && <Spinner />} Apply
              </button>
            </div>
          </div>
        </div>
      )}
      {error && <p className="text-xs text-red-600">{error}</p>}
      {applied && (
        <div className="rounded-md border border-slate-200 bg-white p-2 text-xs">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="text-slate-600">
              AI edit applied: <span className="italic">“{applied.instruction}”</span>
            </span>
            <button type="button" className="text-violet-700 hover:underline" onClick={() => setShowDiff((s) => !s)}>
              {showDiff ? 'Hide changes' : 'Show changes'}
            </button>
            <button type="button" className="font-medium text-slate-700 hover:underline" onClick={undo}>
              Undo
            </button>
            <button
              type="button"
              aria-label="Dismiss"
              className="ml-auto text-slate-400 hover:text-slate-600"
              onClick={() => setApplied(null)}
            >
              ✕
            </button>
          </div>
          {showDiff && <DiffView changes={diff(applied.before, applied.after)} />}
        </div>
      )}
    </div>
  )

  return children({ button, panel })
}
