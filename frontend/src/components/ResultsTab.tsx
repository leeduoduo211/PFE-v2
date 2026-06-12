import { Suspense, lazy } from 'react'
import type { ResultPayload, RunSummary } from '../api/types'
import { fmt, fmtSigned } from './inputs'
import { PageHeader } from './StepTabs'

// Plotly is ~1.5MB gzipped — load it only when a result is actually shown.
const PfeChart = lazy(() =>
  import('./PfeChart').then((m) => ({ default: m.PfeChart })),
)

function downloadCsv(result: ResultPayload) {
  const rows = [
    ['time_years', `time_${result.period_label}`, 'pfe', 'epe'],
    ...result.time_points.map((t, i) => [
      t,
      result.time_points_in_periods[i],
      result.pfe_curve[i],
      result.epe_curve[i],
    ]),
  ]
  const blob = new Blob([rows.map((r) => r.join(',')).join('\n')], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'pfe_profile.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

export function ResultsTab({
  run,
  result,
  tradeIds,
  onGoConfig,
}: {
  run: RunSummary | null
  result: ResultPayload | null
  tradeIds: string[]
  onGoConfig: () => void
}) {
  if (!run) {
    return (
      <>
        <PageHeader title="Results" subtitle="Peak PFE, EPE, and per-trade contribution." />
        <div className="card" style={{ textAlign: 'center', padding: '48px 20px' }}>
          <div style={{ fontSize: 28, color: 'var(--fg4)', marginBottom: 8 }}>○</div>
          <div style={{ fontSize: 14, color: 'var(--fg2)' }}>
            No results yet. Configure and run PFE in the Configuration tab.
          </div>
          <button className="btn btn-secondary btn-sm" style={{ marginTop: 14 }} onClick={onGoConfig}>
            Go to Configuration
          </button>
        </div>
      </>
    )
  }

  if (run.status === 'failed') {
    return (
      <>
        <PageHeader title="Results" subtitle={run.label ?? run.run_id} />
        <div className="error-banner">
          Run failed: <span className="mono">{run.error}</span>
        </div>
      </>
    )
  }

  if (run.status !== 'completed' || !result) {
    return (
      <>
        <PageHeader title="Results" subtitle={run.label ?? run.run_id} />
        <div className="card">
          <h3>Running nested Monte Carlo…</h3>
          <div className="row">
            <div className="progress">
              <div style={{ width: `${Math.round(run.progress * 100)}%` }} />
            </div>
            <span className="mono" style={{ fontSize: 13 }}>
              {Math.round(run.progress * 100)}%
            </span>
          </div>
        </div>
      </>
    )
  }

  const cfg = result.config
  const perTrade = result.per_trade_t0_mtm ?? []
  const netMtm = perTrade.reduce((s, v) => s + v, 0)
  const peakIdx = result.pfe_curve.indexOf(Math.max(...result.pfe_curve))
  const periodCap = result.period_label.charAt(0).toUpperCase() + result.period_label.slice(1, -1)

  return (
    <>
      <PageHeader
        title="Results"
        subtitle={`${run.label ?? run.run_id} · ${fmt(cfg.n_outer)} outer × ${fmt(cfg.n_inner)} inner · ${cfg.grid_frequency} · seed ${cfg.seed} · ${result.computation_time.toFixed(1)}s`}
        right={
          <button className="btn btn-secondary btn-sm" onClick={() => downloadCsv(result)}>
            Export CSV
          </button>
        }
      />

      <div className="kpi-grid">
        <div className="kpi kpi--red">
          <div className="kpi-label">Peak PFE</div>
          <div className="kpi-value">{fmt(result.peak_pfe)}</div>
          <div className="kpi-sub">{Math.round(cfg.confidence_level * 100)}th percentile</div>
        </div>
        <div className="kpi kpi--accent">
          <div className="kpi-label">EEPE</div>
          <div className="kpi-value">{fmt(result.eepe)}</div>
          <div className="kpi-sub">Basel III effective EPE</div>
        </div>
        <div className="kpi kpi--green">
          <div className="kpi-label">Net t=0 MtM</div>
          <div className="kpi-value">{fmtSigned(netMtm)}</div>
          <div className="kpi-sub">{perTrade.length} trades netted</div>
        </div>
        <div className="kpi kpi--amber">
          <div className="kpi-label">Peak time</div>
          <div className="kpi-value">
            {periodCap} {Math.round(result.time_points_in_periods[peakIdx])}
          </div>
          <div className="kpi-sub">
            of {Math.round(result.time_points_in_periods[result.time_points_in_periods.length - 1])}{' '}
            {result.period_label}
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Exposure profile</h3>
        <div className="card-sub">
          PFE {Math.round(cfg.confidence_level * 100)}% (red) and EPE (blue) over the simulation
          horizon.
        </div>
        <Suspense fallback={<div style={{ height: 320 }} />}>
          <PfeChart result={result} />
        </Suspense>
      </div>

      {perTrade.length > 0 && (
        <div className="card">
          <h3>Per-trade t=0 MtM</h3>
          <table className="pfe">
            <thead>
              <tr>
                <th>Trade</th>
                <th className="num">t=0 MtM</th>
                <th className="num">% of gross</th>
              </tr>
            </thead>
            <tbody>
              {perTrade.map((v, i) => {
                const grossAbs = perTrade.reduce((s, x) => s + Math.abs(x), 0)
                return (
                  <tr key={i}>
                    <td>{tradeIds[i] ?? `Trade ${i + 1}`}</td>
                    <td className={'num ' + (v >= 0 ? 'pos' : 'neg')}>{fmtSigned(v)}</td>
                    <td className="num" style={{ color: 'var(--fg4)' }}>
                      {grossAbs > 0 ? ((Math.abs(v) / grossAbs) * 100).toFixed(1) : '0.0'}%
                    </td>
                  </tr>
                )
              })}
              <tr style={{ fontWeight: 600 }}>
                <td>Total</td>
                <td className={'num ' + (netMtm >= 0 ? 'pos' : 'neg')}>{fmtSigned(netMtm)}</td>
                <td className="num" style={{ color: 'var(--fg4)' }}>
                  100%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
