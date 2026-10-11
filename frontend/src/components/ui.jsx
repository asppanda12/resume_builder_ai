const buttonBase =
  'inline-flex items-center justify-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium shadow-sm transition disabled:cursor-not-allowed disabled:opacity-50'

export const buttonStyles = {
  primary: `${buttonBase} bg-emerald-700 text-white hover:bg-emerald-800`,
  secondary: `${buttonBase} border border-slate-300 bg-white text-slate-700 hover:bg-slate-50`,
  link: 'text-xs font-medium text-slate-500 hover:text-red-600',
}

const inputClass =
  'mt-1 w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-800 shadow-sm placeholder:text-slate-400 focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600'

export function Card({ title, actions, children }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      {(title || actions) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600">{title}</h2>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}

export function TextField({ label, value, onChange, placeholder, type = 'text' }) {
  return (
    <label className="block text-xs font-medium text-slate-600">
      {label}
      <input
        type={type}
        className={inputClass}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  )
}

export function TextArea({ label, value, onChange, placeholder, rows = 3, hint }) {
  return (
    <label className="block text-xs font-medium text-slate-600">
      {label}
      {hint && <span className="ml-1 font-normal text-slate-400">({hint})</span>}
      <textarea
        className={inputClass}
        rows={rows}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  )
}

// Edits a string list as one entry per line. Blank lines are kept while typing and dropped by the backend.
export function LinesField({ label, lines, onChange, placeholder, rows = 4 }) {
  return (
    <TextArea
      label={label}
      hint="one per line"
      rows={rows}
      value={lines.join('\n')}
      placeholder={placeholder}
      onChange={(text) => onChange(text.split('\n'))}
    />
  )
}

export function ItemCard({ title, onRemove, actions, children }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-slate-500">{title}</span>
        <div className="flex items-center gap-2">
          {actions}
          <button type="button" className={buttonStyles.link} onClick={onRemove}>
            Remove
          </button>
        </div>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

export function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent"
    />
  )
}
