import { useState } from 'react'

/** Numeric input that commits only finite values, reverting bad drafts on blur. */
export function NumInput({
  value,
  onCommit,
  className,
}: {
  value: number
  onCommit: (v: number) => void
  className?: string
}) {
  const [draft, setDraft] = useState<string | null>(null)
  return (
    <input
      className={className ?? 'inp'}
      value={draft ?? String(value)}
      onChange={(e) => {
        setDraft(e.target.value)
        const n = Number(e.target.value)
        if (e.target.value.trim() !== '' && Number.isFinite(n)) onCommit(n)
      }}
      onBlur={() => setDraft(null)}
    />
  )
}

/** Comma-separated list of numbers (float_list / schedule registry fields). */
export function NumListInput({
  value,
  onCommit,
}: {
  value: number[]
  onCommit: (v: number[]) => void
}) {
  const [draft, setDraft] = useState<string | null>(null)
  return (
    <input
      className="inp"
      value={draft ?? value.join(', ')}
      onChange={(e) => {
        setDraft(e.target.value)
        const parts = e.target.value.split(',').map((s) => Number(s.trim()))
        if (parts.length > 0 && parts.every((n) => Number.isFinite(n))) onCommit(parts)
      }}
      onBlur={() => setDraft(null)}
    />
  )
}

export function fmt(n: number, digits = 0): string {
  return n.toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function fmtSigned(n: number, digits = 0): string {
  return (n >= 0 ? '+' : '−') + fmt(Math.abs(n), digits)
}
