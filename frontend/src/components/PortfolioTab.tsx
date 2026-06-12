import type { MarketState, RegistryPayload, TradeSpec } from '../api/types'
import { PageHeader } from './StepTabs'
import { TradeForm, defaultParams } from './TradeForm'

export function PortfolioTab({
  registry,
  market,
  portfolio,
  setPortfolio,
  selectedId,
  onSelect,
  onPreviewMtm,
  previewError,
}: {
  registry: RegistryPayload
  market: MarketState
  portfolio: TradeSpec[]
  setPortfolio: (p: TradeSpec[]) => void
  selectedId: string | null
  onSelect: (id: string) => void
  onPreviewMtm: () => void
  previewError: string | null
}) {
  const selected = portfolio.find((t) => t.trade_id === selectedId) ?? portfolio[0]

  const nextId = () => {
    let n = portfolio.length + 1
    while (portfolio.some((t) => t.trade_id === `TRD_${String(n).padStart(3, '0')}`)) n++
    return `TRD_${String(n).padStart(3, '0')}`
  }

  const addTrade = () => {
    const type = 'VanillaOption'
    const trade: TradeSpec = {
      trade_id: nextId(),
      instrument_type: type,
      direction: 'long',
      params: defaultParams(registry.instruments[type], market.asset_names),
      modifiers: [],
    }
    setPortfolio([...portfolio, trade])
    onSelect(trade.trade_id)
  }

  const replace = (old: TradeSpec, next: TradeSpec) => {
    setPortfolio(portfolio.map((t) => (t === old ? next : t)))
    if (old.trade_id === selectedId && next.trade_id !== old.trade_id) onSelect(next.trade_id)
  }

  return (
    <>
      <PageHeader
        title="Portfolio"
        subtitle="Add trades and stack modifiers. Each modifier wraps the previous payoff."
        right={
          <div className="row" style={{ gap: 6 }}>
            <button className="btn btn-secondary btn-sm" disabled={!portfolio.length} onClick={onPreviewMtm}>
              Preview t=0 MtM
            </button>
            <button className="btn btn-primary" onClick={addTrade}>
              + Add trade
            </button>
          </div>
        }
      />

      {previewError && (
        <div className="error-banner">
          <span className="mono">{previewError}</span>
        </div>
      )}

      {portfolio.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px 20px' }}>
          <div style={{ fontSize: 28, color: 'var(--fg4)', marginBottom: 8 }}>○</div>
          <div style={{ fontSize: 14, color: 'var(--fg2)' }}>
            Portfolio is empty. Add a trade to get started.
          </div>
          <button className="btn btn-primary" style={{ marginTop: 14 }} onClick={addTrade}>
            + Add trade
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 16 }}>
          <div className="card" style={{ padding: 14, alignSelf: 'start' }}>
            <div className="sb-overline" style={{ marginTop: 0 }}>
              Trades
            </div>
            {portfolio.map((t) => (
              <div
                key={t.trade_id}
                className={'sb-item' + (t === selected ? ' sel' : '')}
                onClick={() => onSelect(t.trade_id)}
                style={{ marginBottom: 4 }}
              >
                <span>{t.trade_id}</span>
                <span className={'tag ' + (t.direction === 'long' ? 'tag-long' : 'tag-short')}>
                  {t.direction === 'long' ? 'L' : 'S'}
                </span>
              </div>
            ))}
          </div>

          {selected && (
            <TradeForm
              trade={selected}
              registry={registry}
              assetNames={market.asset_names}
              onChange={(t) => replace(selected, t)}
              onClone={() => {
                const clone = { ...selected, trade_id: nextId(), params: { ...selected.params } }
                setPortfolio([...portfolio, clone])
                onSelect(clone.trade_id)
              }}
              onDelete={() => setPortfolio(portfolio.filter((t) => t !== selected))}
            />
          )}
        </div>
      )}
    </>
  )
}
