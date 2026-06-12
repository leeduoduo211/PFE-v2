import type { RunSummary, TradeSpec } from '../api/types'
import { fmt, fmtSigned } from './inputs'

export function Sidebar({
  trades,
  selectedId,
  onSelectTrade,
  runs,
  activeRunId,
  onSelectRun,
  t0Mtm,
}: {
  trades: TradeSpec[]
  selectedId: string | null
  onSelectTrade: (id: string) => void
  runs: RunSummary[]
  activeRunId: string | null
  onSelectRun: (id: string) => void
  t0Mtm: number[] | null
}) {
  const notional = (t: TradeSpec) => Number(t.params.notional ?? 0)
  const gross = trades.reduce((s, t) => s + Math.abs(notional(t)), 0)
  const net = trades.reduce(
    (s, t) => s + (t.direction === 'long' ? notional(t) : -notional(t)),
    0,
  )
  const maxMat = trades.reduce((m, t) => Math.max(m, Number(t.params.maturity ?? 0)), 0)

  return (
    <aside className="sb">
      <div className="sb-brand">
        <div className="sb-logo">P</div>
        <div>
          <div className="sb-title">PFE-v2</div>
          <div className="sb-sub">Monte Carlo Engine</div>
        </div>
      </div>

      <div className="sb-overline">Portfolio ({trades.length} trades)</div>
      <div className="sb-summary">
        <div>
          <span>Gross notl.</span>
          <span className="mono">{(gross / 1e6).toFixed(2)}M</span>
        </div>
        <div>
          <span>Net notl.</span>
          <span className="mono">
            {net >= 0 ? '+' : ''}
            {(net / 1e6).toFixed(2)}M
          </span>
        </div>
        <div>
          <span>Max maturity</span>
          <span className="mono">{maxMat.toFixed(2)}y</span>
        </div>
      </div>
      {trades.map((t, i) => (
        <div
          key={t.trade_id}
          className={'sb-item' + (t.trade_id === selectedId ? ' sel' : '')}
          onClick={() => onSelectTrade(t.trade_id)}
        >
          <span style={{ color: 'var(--fg1)', fontWeight: 500 }}>{t.trade_id}</span>
          <span className="row" style={{ gap: 6 }}>
            <span className={'tag ' + (t.direction === 'long' ? 'tag-long' : 'tag-short')}>
              {t.direction === 'long' ? 'L' : 'S'}
            </span>
            {t0Mtm && t0Mtm[i] !== undefined && (
              <span className="sb-num">{fmtSigned(t0Mtm[i])}</span>
            )}
          </span>
        </div>
      ))}

      <div className="sb-overline">Run history</div>
      {runs.length === 0 && (
        <div style={{ fontSize: 11, color: 'var(--fg4)', padding: '2px 8px' }}>
          No runs yet.
        </div>
      )}
      {runs.map((r) => (
        <div
          key={r.run_id}
          className={'sb-item' + (r.run_id === activeRunId ? ' sel' : '')}
          onClick={() => onSelectRun(r.run_id)}
        >
          <span>
            {r.status === 'completed' ? '●' : r.status === 'failed' ? '✕' : '◌'}{' '}
            {r.label ?? r.run_id}
          </span>
          <span className="sb-num">
            {r.status === 'completed' && r.peak_pfe !== null
              ? fmt(r.peak_pfe / 1e6, 2) + 'M'
              : r.status === 'failed'
                ? 'failed'
                : `${Math.round(r.progress * 100)}%`}
          </span>
        </div>
      ))}
    </aside>
  )
}
