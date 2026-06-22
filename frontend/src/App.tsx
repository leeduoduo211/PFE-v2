import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError } from './api/client'
import type {
  MarketState,
  RegistryPayload,
  ResultPayload,
  RunSummary,
  TradeSpec,
} from './api/types'
import { ConfigTab, type AppConfig } from './components/ConfigTab'
import { MarketTab } from './components/MarketTab'
import { PortfolioTab } from './components/PortfolioTab'
import { ResultsTab } from './components/ResultsTab'
import { Sidebar } from './components/Sidebar'
import { StepTabs } from './components/StepTabs'

const DEFAULT_MARKET: MarketState = {
  spots: [100.0, 50.0],
  vols: [0.2, 0.3],
  rates: [0.05, 0.05],
  domestic_rate: 0.05,
  corr_matrix: [
    [1.0, 0.5],
    [0.5, 1.0],
  ],
  asset_names: ['AAPL', 'XYZ'],
  asset_classes: ['EQUITY', 'EQUITY'],
}

const DEFAULT_CONFIG: AppConfig = {
  n_outer: 1000,
  n_inner: 1000,
  seed: 42,
  grid_frequency: 'weekly',
  confidence_level: 0.95,
  n_workers: 1,
  margined: false,
  mpor_days: 10,
  antithetic: false,
}

export default function App() {
  const [registry, setRegistry] = useState<RegistryPayload | null>(null)
  const [registryError, setRegistryError] = useState<string | null>(null)
  const [step, setStep] = useState(1)
  const [market, setMarket] = useState<MarketState>(DEFAULT_MARKET)
  const [portfolio, setPortfolio] = useState<TradeSpec[]>([])
  const [config, setConfig] = useState(DEFAULT_CONFIG)
  const [selectedTradeId, setSelectedTradeId] = useState<string | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [result, setResult] = useState<ResultPayload | null>(null)
  const [t0Mtm, setT0Mtm] = useState<number[] | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  // Trade ids snapshotted per run, so the per-trade table stays correct
  // even if the portfolio is edited while a run is in flight.
  const runTradeIds = useRef<Record<string, string[]>>({})

  useEffect(() => {
    api.registry().then(setRegistry, (e) => setRegistryError(String(e)))
    api.listRuns().then(setRuns, () => {})
  }, [])

  const activeRun = runs.find((r) => r.run_id === activeRunId) ?? null

  // Stream progress via Server-Sent Events while a run is active; fetch the
  // result on completion. Works for both in-flight and already-finished runs
  // (a terminal run emits one event, then the stream closes).
  useEffect(() => {
    if (!activeRunId) return
    const es = new EventSource(`/api/runs/${activeRunId}/events`)
    let cancelled = false

    es.onmessage = async (ev) => {
      if (cancelled) return
      // The stream emits run summaries, or {error} for an unknown id. Both
      // shapes carry an `error` key, so discriminate on `status` instead.
      const payload = JSON.parse(ev.data) as Record<string, unknown>
      if (typeof payload.status !== 'string') {
        es.close()
        return
      }
      const status = payload as unknown as RunSummary
      setRuns((rs) => {
        const others = rs.filter((r) => r.run_id !== status.run_id)
        return [status, ...others].sort((a, b) => b.submitted_at - a.submitted_at)
      })
      if (status.status === 'completed' || status.status === 'failed') {
        es.close() // terminal — stop the browser from auto-reconnecting
        if (status.status === 'completed') {
          try {
            const res = await api.runResult(activeRunId)
            if (!cancelled) setResult(res)
          } catch {
            /* result fetch failed; the status still shows completed */
          }
        }
      }
    }

    return () => {
      cancelled = true
      es.close()
    }
  }, [activeRunId])

  const submitRun = useCallback(
    async (label: string) => {
      setSubmitting(true)
      setSubmitError(null)
      try {
        const summary = await api.submitRun({
          market,
          portfolio,
          config,
          label: label || null,
        })
        runTradeIds.current[summary.run_id] = portfolio.map((t) => t.trade_id)
        setResult(null)
        setActiveRunId(summary.run_id)
        setRuns((rs) => [summary, ...rs])
        setStep(4)
      } catch (e) {
        setSubmitError(e instanceof ApiError ? e.message : String(e))
      } finally {
        setSubmitting(false)
      }
    },
    [market, portfolio, config],
  )

  const previewMtm = useCallback(async () => {
    setPreviewError(null)
    try {
      const resp = await api.t0Mtm({ market, portfolio, config })
      setT0Mtm(resp.per_trade_t0_mtm)
    } catch (e) {
      setT0Mtm(null)
      setPreviewError(e instanceof ApiError ? e.message : String(e))
    }
  }, [market, portfolio, config])

  const selectRun = useCallback((id: string) => {
    setResult(null)
    setActiveRunId(id)
    setStep(4)
  }, [])

  if (registryError) {
    return (
      <div style={{ padding: 40 }}>
        <div className="error-banner">
          Cannot reach the PFE-v2 API ({registryError}). Start it with{' '}
          <span className="mono">python3 -m uvicorn api.app:app</span> and reload.
        </div>
      </div>
    )
  }
  if (!registry) return <div style={{ padding: 40, color: 'var(--fg3)' }}>Loading registry…</div>

  return (
    <div className="app">
      <Sidebar
        trades={portfolio}
        selectedId={selectedTradeId}
        onSelectTrade={(id) => {
          setSelectedTradeId(id)
          setStep(2)
        }}
        runs={runs}
        activeRunId={activeRunId}
        onSelectRun={selectRun}
        t0Mtm={t0Mtm}
      />
      <main className="main">
        <StepTabs
          step={step}
          setStep={setStep}
          tradeCount={portfolio.length}
          hasResults={result !== null}
        />
        {step === 1 && <MarketTab market={market} setMarket={setMarket} />}
        {step === 2 && (
          <PortfolioTab
            registry={registry}
            market={market}
            portfolio={portfolio}
            setPortfolio={setPortfolio}
            selectedId={selectedTradeId}
            onSelect={setSelectedTradeId}
            onPreviewMtm={previewMtm}
            previewError={previewError}
          />
        )}
        {step === 3 && (
          <ConfigTab
            config={config}
            setConfig={setConfig}
            tradeCount={portfolio.length}
            onRun={submitRun}
            submitting={submitting}
            submitError={submitError}
          />
        )}
        {step === 4 && (
          <ResultsTab
            run={activeRun}
            result={result}
            tradeIds={activeRunId ? (runTradeIds.current[activeRunId] ?? []) : []}
            onGoConfig={() => setStep(3)}
          />
        )}
      </main>
    </div>
  )
}
