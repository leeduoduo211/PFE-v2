import { useState } from 'react'
import type { ConfigState } from '../api/types'
import { NumInput } from './inputs'
import { PageHeader } from './StepTabs'

export type AppConfig = Required<
  Pick<
    ConfigState,
    | 'n_outer'
    | 'n_inner'
    | 'seed'
    | 'grid_frequency'
    | 'confidence_level'
    | 'n_workers'
    | 'margined'
    | 'mpor_days'
    | 'antithetic'
  >
>

export function ConfigTab({
  config,
  setConfig,
  tradeCount,
  onRun,
  submitting,
  submitError,
}: {
  config: AppConfig
  setConfig: (c: AppConfig) => void
  tradeCount: number
  onRun: (label: string) => void
  submitting: boolean
  submitError: string | null
}) {
  const [label, setLabel] = useState('')
  const update = (patch: Partial<AppConfig>) => setConfig({ ...config, ...patch })

  return (
    <>
      <PageHeader title="Configuration" subtitle="Simulation parameters for the nested Monte Carlo run." />

      <div className="card">
        <h3>Sampling</h3>
        <div className="grid-3">
          <div className="field">
            <label>Outer paths</label>
            <NumInput value={config.n_outer} onCommit={(v) => update({ n_outer: v })} />
            <small>World scenarios (market futures).</small>
          </div>
          <div className="field">
            <label>Inner paths</label>
            <NumInput value={config.n_inner} onCommit={(v) => update({ n_inner: v })} />
            <small>Per-state pricer revaluations.</small>
          </div>
          <div className="field">
            <label>Seed</label>
            <NumInput value={config.seed} onCommit={(v) => update({ seed: v })} />
            <small>Reproducibility.</small>
          </div>
          <div className="field">
            <label>Grid frequency</label>
            <select
              className="sel"
              value={config.grid_frequency}
              onChange={(e) => update({ grid_frequency: e.target.value as ConfigState['grid_frequency'] })}
            >
              <option>weekly</option>
              <option>daily</option>
              <option>monthly</option>
            </select>
            <small>Exposure sampling granularity.</small>
          </div>
          <div className="field">
            <label>Confidence</label>
            <NumInput value={config.confidence_level} onCommit={(v) => update({ confidence_level: v })} />
            <small>PFE quantile level.</small>
          </div>
          <div className="field">
            <label>Workers</label>
            <NumInput value={config.n_workers} onCommit={(v) => update({ n_workers: v })} />
            <small>Threads across time steps.</small>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Variance reduction &amp; margining</h3>
        <div className="grid-2">
          <label className="check-row">
            <input
              type="checkbox"
              checked={config.antithetic}
              onChange={(e) => update({ antithetic: e.target.checked })}
            />
            Antithetic variates
            <span className="hint">pair Z and −Z (requires even inner paths)</span>
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={config.margined}
              onChange={(e) => update({ margined: e.target.checked })}
            />
            Margined exposure
            <span className="hint">MPoR lookback collateral model</span>
          </label>
          {config.margined && (
            <div className="field">
              <label>MPoR (days)</label>
              <NumInput value={config.mpor_days} onCommit={(v) => update({ mpor_days: v })} />
              <small>Margin period of risk.</small>
            </div>
          )}
        </div>
      </div>

      {submitError && (
        <div className="error-banner">
          <span className="mono">{submitError}</span>
        </div>
      )}

      <div className="banner">
        <div className="row" style={{ flex: 1 }}>
          <span>
            {tradeCount} trade{tradeCount === 1 ? '' : 's'} ·{' '}
            <span className="mono">
              {config.n_outer.toLocaleString()} × {config.n_inner.toLocaleString()}
            </span>{' '}
            · {config.grid_frequency}
          </span>
          <input
            className="inp"
            style={{ width: 220, marginLeft: 'auto' }}
            placeholder="Run label (optional)"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
        </div>
        <button
          className="btn btn-primary"
          style={{ marginLeft: 12 }}
          disabled={submitting || tradeCount === 0}
          onClick={() => onRun(label)}
        >
          {submitting ? 'Submitting…' : 'Run PFE →'}
        </button>
      </div>
    </>
  )
}
