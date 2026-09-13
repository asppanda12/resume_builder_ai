import { buttonStyles, Card, Spinner, TextArea } from './ui'

const MIN_JD_LENGTH = 30

function tone(score) {
  if (score.meets_threshold) return { text: 'text-emerald-700', bar: 'bg-emerald-600' }
  if (score.overall_score >= score.threshold - 20) return { text: 'text-amber-600', bar: 'bg-amber-500' }
  return { text: 'text-red-600', bar: 'bg-red-500' }
}

function Chips({ items, className }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((k) => (
        <span key={k} className={`rounded-full px-2 py-0.5 text-xs font-medium ${className}`}>
          {k}
        </span>
      ))}
    </div>
  )
}

function ScoreView({ score }) {
  const t = tone(score)
  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-end gap-3">
        <span className={`text-4xl font-bold tabular-nums ${t.text}`}>{Math.round(score.overall_score)}</span>
        <span className="pb-1 text-sm text-slate-500">
          / 100 · keywords {Math.round(score.keyword_score)} · semantic {Math.round(score.semantic_score)} · target{' '}
          {Math.round(score.threshold)}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full ${t.bar}`} style={{ width: `${score.overall_score}%` }} />
      </div>
      {score.matched_keywords.length > 0 && (
        <div>
          <h3 className="mb-1 text-xs font-semibold text-slate-600">Matched keywords</h3>
          <Chips items={score.matched_keywords} className="bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200" />
        </div>
      )}
      {score.missing_keywords.length > 0 && (
        <div>
          <h3 className="mb-1 text-xs font-semibold text-slate-600">Missing keywords</h3>
          <Chips items={score.missing_keywords} className="bg-red-50 text-red-700 ring-1 ring-red-200" />
        </div>
      )}
      {score.suggestions.length > 0 && (
        <div>
          <h3 className="mb-1 text-xs font-semibold text-slate-600">Suggestions</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {score.suggestions.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function OptimizationResult({ result, onApply, onDiscard }) {
  return (
    <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm">
      <p className="text-slate-800">{result.message}</p>
      <div className="mt-2 flex gap-2">
        {result.optimized ? (
          <>
            <button type="button" className={buttonStyles.primary} onClick={onApply}>
              Apply optimized resume
            </button>
            <button type="button" className={buttonStyles.secondary} onClick={onDiscard}>
              Discard
            </button>
          </>
        ) : (
          <button type="button" className={buttonStyles.secondary} onClick={onDiscard}>
            Dismiss
          </button>
        )}
      </div>
    </div>
  )
}

export default function AtsPanel({ jd, onJdChange, score, optimization, busy, onScore, onOptimize, onApply, onDiscard }) {
  const jdTooShort = jd.trim().length < MIN_JD_LENGTH
  const disabled = jdTooShort || Boolean(busy)
  const shownScore = optimization ? optimization.final_score : score

  return (
    <Card title="ATS match">
      <TextArea
        label="Job description"
        rows={8}
        value={jd}
        onChange={onJdChange}
        placeholder="Paste the full job posting here…"
      />
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button type="button" className={buttonStyles.primary} disabled={disabled} onClick={onScore}>
          {busy === 'score' && <Spinner />} Score resume
        </button>
        <button type="button" className={buttonStyles.secondary} disabled={disabled} onClick={onOptimize}>
          {busy === 'optimize' && <Spinner />} Optimize with AI
        </button>
        {jdTooShort && jd.length > 0 && <span className="text-xs text-slate-500">Paste the full job description.</span>}
      </div>
      {busy === 'optimize' && (
        <p className="mt-2 text-xs text-slate-500">Rewriting and re-scoring against the job. This can take a minute or two.</p>
      )}
      {optimization && <OptimizationResult result={optimization} onApply={onApply} onDiscard={onDiscard} />}
      {shownScore && <ScoreView score={shownScore} />}
    </Card>
  )
}
