import type { MarketState } from '../api/types'
import { NumInput } from './inputs'
import { PageHeader } from './StepTabs'

const MAX_ASSETS = 10

/** Resize a correlation matrix, identity-extending for new assets. */
function resizeCorr(corr: number[][], n: number): number[][] {
  return Array.from({ length: n }, (_, i) =>
    Array.from({ length: n }, (_, j) => (i === j ? 1.0 : (corr[i]?.[j] ?? 0.0))),
  )
}

export function MarketTab({
  market,
  setMarket,
}: {
  market: MarketState
  setMarket: (m: MarketState) => void
}) {
  const n = market.asset_names.length

  const update = (patch: Partial<MarketState>) => setMarket({ ...market, ...patch })

  const setAt = (key: 'spots' | 'vols' | 'rates', i: number, v: number) => {
    const arr = [...market[key]]
    arr[i] = v
    update({ [key]: arr })
  }

  const addAsset = () => {
    const name = `ASSET${n + 1}`
    update({
      asset_names: [...market.asset_names, name],
      asset_classes: [...market.asset_classes, 'EQUITY'],
      spots: [...market.spots, 100.0],
      vols: [...market.vols, 0.2],
      rates: [...market.rates, market.domestic_rate],
      corr_matrix: resizeCorr(market.corr_matrix, n + 1),
    })
  }

  const removeAsset = (i: number) => {
    const drop = <T,>(arr: T[]) => arr.filter((_, k) => k !== i)
    update({
      asset_names: drop(market.asset_names),
      asset_classes: drop(market.asset_classes),
      spots: drop(market.spots),
      vols: drop(market.vols),
      rates: drop(market.rates),
      corr_matrix: drop(market.corr_matrix).map((row) => drop(row)),
    })
  }

  const setCorr = (i: number, j: number, v: number) => {
    const m = market.corr_matrix.map((row) => [...row])
    m[i][j] = v
    m[j][i] = v // keep symmetric
    update({ corr_matrix: m })
  }

  return (
    <>
      <PageHeader
        title="Market Data"
        subtitle="Define assets, spot prices, volatilities, and correlation structure."
      />

      <div className="card">
        <h3>Assets</h3>
        <div className="card-sub">Names are free-form — trades reference them by name.</div>
        <table className="pfe">
          <thead>
            <tr>
              <th>Name</th>
              <th>Class</th>
              <th className="num">Spot</th>
              <th className="num">Vol (ann.)</th>
              <th className="num">Rate</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {market.asset_names.map((name, i) => (
              <tr key={i}>
                <td>
                  <input
                    className="inp"
                    style={{ fontFamily: 'var(--font-sans)', fontWeight: 500 }}
                    value={name}
                    onChange={(e) => {
                      const names = [...market.asset_names]
                      names[i] = e.target.value
                      update({ asset_names: names })
                    }}
                  />
                </td>
                <td>
                  <select
                    className="sel"
                    value={market.asset_classes[i]}
                    onChange={(e) => {
                      const classes = [...market.asset_classes]
                      classes[i] = e.target.value
                      update({ asset_classes: classes })
                    }}
                  >
                    <option>EQUITY</option>
                    <option>FX</option>
                  </select>
                </td>
                <td className="num">
                  <NumInput value={market.spots[i]} onCommit={(v) => setAt('spots', i, v)} />
                </td>
                <td className="num">
                  <NumInput value={market.vols[i]} onCommit={(v) => setAt('vols', i, v)} />
                </td>
                <td className="num">
                  <NumInput value={market.rates[i]} onCommit={(v) => setAt('rates', i, v)} />
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    style={{ color: 'var(--red)' }}
                    disabled={n <= 1}
                    onClick={() => removeAsset(i)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn btn-secondary btn-sm" disabled={n >= MAX_ASSETS} onClick={addAsset}>
            + Add asset
          </button>
          <small style={{ color: 'var(--fg4)' }}>
            {n} of {MAX_ASSETS} asset cap.
          </small>
          <div className="field" style={{ marginLeft: 'auto', width: 160 }}>
            <label>Domestic rate</label>
            <NumInput
              value={market.domestic_rate}
              onCommit={(v) => update({ domestic_rate: v })}
            />
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Correlation matrix</h3>
        <div className="card-sub">
          Symmetric — editing a cell mirrors it. Must be positive semi-definite; validated by
          the engine on preview/run.
        </div>
        <table className="pfe" style={{ maxWidth: 90 + n * 90 }}>
          <thead>
            <tr>
              <th></th>
              {market.asset_names.map((a) => (
                <th key={a} className="num">
                  {a}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {market.corr_matrix.map((row, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 500 }}>{market.asset_names[i]}</td>
                {row.map((v, j) =>
                  i === j ? (
                    <td key={j} className="num" style={{ color: 'var(--fg4)' }}>
                      1.00
                    </td>
                  ) : (
                    <td
                      key={j}
                      className="num"
                      style={{
                        background: `rgba(${v > 0 ? '59,130,246' : '239,68,68'},${Math.abs(v) * 0.12})`,
                      }}
                    >
                      <NumInput
                        value={v}
                        onCommit={(x) => setCorr(i, j, x)}
                        className="inp"
                      />
                    </td>
                  ),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
