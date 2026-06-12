import type { ReactNode } from 'react'

export function StepTabs({
  step,
  setStep,
  tradeCount,
  hasResults,
}: {
  step: number
  setStep: (n: number) => void
  tradeCount: number
  hasResults: boolean
}) {
  const steps = [
    { n: 1, label: 'Market Data', done: true },
    { n: 2, label: `Portfolio (${tradeCount})`, done: tradeCount > 0 },
    { n: 3, label: 'Configuration', done: tradeCount > 0 },
    { n: 4, label: 'Results', done: hasResults },
  ]
  const glyph = (done: boolean, active: boolean) => (active || done ? '●' : '○')
  return (
    <div className="tabs">
      {steps.map((s) => (
        <div
          key={s.n}
          className={'tab' + (step === s.n ? ' active' : '')}
          onClick={() => setStep(s.n)}
        >
          <span
            style={{
              marginRight: 6,
              color: step === s.n || s.done ? 'var(--blue)' : 'var(--fg4)',
            }}
          >
            {glyph(s.done, step === s.n)}
          </span>
          {s.n}. {s.label}
        </div>
      ))}
    </div>
  )
}

export function PageHeader({
  title,
  subtitle,
  right,
}: {
  title: string
  subtitle: string
  right?: ReactNode
}) {
  return (
    <div className="between" style={{ marginBottom: 4 }}>
      <div>
        <h1 className="page-title">{title}</h1>
        <div className="page-sub">{subtitle}</div>
      </div>
      {right}
    </div>
  )
}
