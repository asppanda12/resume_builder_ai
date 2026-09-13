import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { buttonStyles, Card, Spinner } from './ui'

// The rendered page is ~210mm (794px) wide plus margin; the iframe is scaled down to fit the column.
const FRAME_WIDTH = 860
const FRAME_HEIGHT = 1180

export default function Preview({ resume, theme, themes, onThemeChange, onDownload, downloading, banner }) {
  const [html, setHtml] = useState('')
  const [error, setError] = useState(null)
  const [scale, setScale] = useState(0.6)
  const latestRequest = useRef(0)
  const wrapper = useRef(null)

  // Debounced re-render; ignores responses that arrive after a newer request was sent.
  useEffect(() => {
    const id = ++latestRequest.current
    const timer = setTimeout(async () => {
      try {
        const rendered = await api.previewHtml(resume, theme)
        if (id === latestRequest.current) {
          setHtml(rendered)
          setError(null)
        }
      } catch (e) {
        if (id === latestRequest.current) setError(e.message)
      }
    }, 350)
    return () => clearTimeout(timer)
  }, [resume, theme])

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => setScale(Math.min(1, entry.contentRect.width / FRAME_WIDTH)))
    observer.observe(wrapper.current)
    return () => observer.disconnect()
  }, [])

  return (
    <Card
      title="Preview"
      actions={
        <>
          <select
            aria-label="Theme"
            className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm shadow-sm"
            value={theme}
            onChange={(e) => onThemeChange(e.target.value)}
          >
            {themes.map((t) => (
              <option key={t.id} value={t.id} title={t.description}>
                {t.name}
              </option>
            ))}
          </select>
          <button type="button" className={buttonStyles.secondary} onClick={onDownload} disabled={downloading}>
            {downloading && <Spinner />} Download PDF
          </button>
        </>
      }
    >
      {banner}
      {error && <p className="mb-2 text-sm text-red-600">Preview failed: {error}</p>}
      <div
        ref={wrapper}
        className="overflow-hidden rounded-md border border-slate-200 bg-slate-300"
        style={{ height: FRAME_HEIGHT * scale }}
      >
        {/* sandbox="" disables scripts inside the rendered resume */}
        <iframe
          title="Resume preview"
          sandbox=""
          srcDoc={html}
          style={{
            width: FRAME_WIDTH,
            height: FRAME_HEIGHT,
            border: 0,
            transform: `scale(${scale})`,
            transformOrigin: 'top left',
          }}
        />
      </div>
    </Card>
  )
}
