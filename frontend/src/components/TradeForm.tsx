import type {
  FieldSpec,
  InstrumentEntry,
  ModifierSpec,
  RegistryPayload,
  TradeSpec,
} from '../api/types'
import { NumInput, NumListInput } from './inputs'

/** Parse registry n_assets: 1 | 3 | "1-5" | "2-5" → [min, max]. */
export function assetRange(nAssets: number | string): [number, number] {
  if (typeof nAssets === 'number') return [nAssets, nAssets]
  const [lo, hi] = String(nAssets).split('-').map(Number)
  return [lo, hi ?? lo]
}

/** Default params for a fresh trade of the given instrument type. */
export function defaultParams(
  entry: InstrumentEntry,
  assetNames: string[],
): Record<string, unknown> {
  const [minAssets] = assetRange(entry.n_assets)
  const params: Record<string, unknown> = {
    notional: 1_000_000,
    maturity: 1.0,
    assets: assetNames.slice(0, minAssets),
  }
  for (const f of entry.fields) params[f.name] = f.default ?? null
  return params
}

const CAT_CLASS: Record<string, string> = {
  European: 'cat-eu',
  'Path-dependent': 'cat-pd',
  'Multi-asset': 'cat-ma',
  Periodic: 'cat-pe',
}

const GROUP_BADGE: Record<string, { cls: string; border: string }> = {
  Barrier: { cls: 'mg-barrier', border: 'b-amber' },
  'Payoff shaper': { cls: 'mg-payoff', border: 'b-green' },
  Structural: { cls: 'mg-struct', border: 'b-purple' },
}

function Field({
  spec,
  value,
  onChange,
  assetNames,
}: {
  spec: FieldSpec
  value: unknown
  onChange: (v: unknown) => void
  assetNames: string[]
}) {
  let control
  switch (spec.type) {
    case 'float':
      control = <NumInput value={Number(value ?? 0)} onCommit={onChange} />
      break
    case 'select':
      control = (
        <select className="sel" value={String(value ?? '')} onChange={(e) => onChange(e.target.value)}>
          {(spec.choices ?? []).map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      )
      break
    case 'float_list':
    case 'schedule':
      control = (
        <NumListInput
          value={Array.isArray(value) ? (value as number[]) : []}
          onCommit={onChange}
        />
      )
      break
    case 'select_list': {
      const items = Array.isArray(value) ? (value as string[]) : []
      control = (
        <div className="row" style={{ gap: 6 }}>
          {items.map((v, i) => (
            <select
              key={i}
              className="sel"
              value={v}
              onChange={(e) => onChange(items.map((x, k) => (k === i ? e.target.value : x)))}
            >
              {(spec.choices ?? []).map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          ))}
        </div>
      )
      break
    }
    case 'asset_select':
    case 'asset_select_optional':
      control = (
        <select className="sel" value={String(value ?? '')} onChange={(e) => onChange(e.target.value)}>
          {spec.type === 'asset_select_optional' && <option value="">(none)</option>}
          {assetNames.map((a) => (
            <option key={a}>{a}</option>
          ))}
        </select>
      )
      break
    default:
      control = (
        <input className="inp" value={String(value ?? '')} onChange={(e) => onChange(e.target.value)} />
      )
  }
  return (
    <div className="field">
      <label>{spec.label}</label>
      {control}
      {spec.help && <small>{spec.help}</small>}
    </div>
  )
}

export function TradeForm({
  trade,
  registry,
  assetNames,
  onChange,
  onDelete,
  onClone,
}: {
  trade: TradeSpec
  registry: RegistryPayload
  assetNames: string[]
  onChange: (t: TradeSpec) => void
  onDelete: () => void
  onClone: () => void
}) {
  const entry = registry.instruments[trade.instrument_type]
  if (!entry) return null
  const [minAssets, maxAssets] = assetRange(entry.n_assets)
  const assets = Array.isArray(trade.params.assets) ? (trade.params.assets as string[]) : []

  const setParam = (name: string, v: unknown) =>
    onChange({ ...trade, params: { ...trade.params, [name]: v } })

  const setInstrumentType = (type: string) =>
    onChange({
      ...trade,
      instrument_type: type,
      params: defaultParams(registry.instruments[type], assetNames),
      modifiers: trade.modifiers, // modifiers wrap any instrument — keep them
    })

  const setModifier = (i: number, mod: ModifierSpec) =>
    onChange({ ...trade, modifiers: trade.modifiers.map((m, k) => (k === i ? mod : m)) })

  const addModifier = (type: string) => {
    const fields = registry.modifiers[type].fields
    const params = Object.fromEntries(fields.map((f) => [f.name, f.default ?? null]))
    onChange({ ...trade, modifiers: [...trade.modifiers, { type, params }] })
  }

  const chain = [...trade.modifiers.map((m) => registry.modifiers[m.type]?.label ?? m.type)]
    .reverse()
    .concat(entry.label)
    .join(' → ')

  return (
    <div className="card">
      <div className="between" style={{ marginBottom: 12 }}>
        <div className="row">
          <span className={'cat ' + (CAT_CLASS[entry.category] ?? 'cat-eu')}>
            {entry.category.toUpperCase()}
          </span>
          <input
            className="inp"
            style={{ width: 180, fontWeight: 600 }}
            value={trade.trade_id}
            onChange={(e) => onChange({ ...trade, trade_id: e.target.value })}
          />
        </div>
        <div className="row" style={{ gap: 6 }}>
          <button className="btn btn-secondary btn-sm" onClick={onClone}>
            Clone
          </button>
          <button className="btn btn-secondary btn-sm" style={{ color: 'var(--red)' }} onClick={onDelete}>
            Delete
          </button>
        </div>
      </div>

      <div className="group b-blue">
        <h4>Instrument &amp; economics</h4>
        <p>Core terms — type, direction, size, underlyings.</p>
      </div>
      <div className="grid-3">
        <div className="field">
          <label>Instrument</label>
          <select className="sel" value={trade.instrument_type} onChange={(e) => setInstrumentType(e.target.value)}>
            {['European', 'Path-dependent', 'Multi-asset', 'Periodic'].map((cat) => (
              <optgroup key={cat} label={cat}>
                {Object.entries(registry.instruments)
                  .filter(([, v]) => v.category === cat)
                  .map(([k, v]) => (
                    <option key={k} value={k}>
                      {v.label}
                    </option>
                  ))}
              </optgroup>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Direction</label>
          <select
            className="sel"
            value={trade.direction}
            onChange={(e) => onChange({ ...trade, direction: e.target.value as 'long' | 'short' })}
          >
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </div>
        <div className="field">
          <label>Notional</label>
          <NumInput value={Number(trade.params.notional ?? 0)} onCommit={(v) => setParam('notional', v)} />
        </div>
        <div className="field">
          <label>Maturity (years)</label>
          <NumInput value={Number(trade.params.maturity ?? 1)} onCommit={(v) => setParam('maturity', v)} />
        </div>
        {assets.map((a, i) => (
          <div className="field" key={i}>
            <label>
              Underlying {maxAssets > 1 ? i + 1 : ''}{' '}
              {assets.length > minAssets && (
                <a
                  style={{ color: 'var(--red)', cursor: 'pointer', fontWeight: 400 }}
                  onClick={() => setParam('assets', assets.filter((_, k) => k !== i))}
                >
                  remove
                </a>
              )}
            </label>
            <select
              className="sel"
              value={a}
              onChange={(e) => setParam('assets', assets.map((x, k) => (k === i ? e.target.value : x)))}
            >
              {assetNames.map((nm) => (
                <option key={nm}>{nm}</option>
              ))}
            </select>
          </div>
        ))}
        {assets.length < maxAssets && (
          <div className="field">
            <label>&nbsp;</label>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => setParam('assets', [...assets, assetNames[0]])}
            >
              + Add underlying
            </button>
          </div>
        )}
      </div>

      {entry.fields.length > 0 && (
        <>
          <div className="group b-blue">
            <h4>{entry.label} terms</h4>
          </div>
          <div className="grid-3">
            {entry.fields.map((f) => (
              <Field
                key={f.name}
                spec={f}
                value={trade.params[f.name]}
                onChange={(v) => setParam(f.name, v)}
                assetNames={assetNames}
              />
            ))}
          </div>
        </>
      )}

      {trade.modifiers.map((mod, i) => {
        const mentry = registry.modifiers[mod.type]
        const badge = GROUP_BADGE[mentry?.group ?? ''] ?? GROUP_BADGE.Structural
        return (
          <div key={i}>
            <div className={'group ' + badge.border}>
              <div className="between">
                <h4>
                  Modifier: {mentry?.label ?? mod.type}
                  <span className={'mg ' + badge.cls}>{(mentry?.group ?? '').toUpperCase()}</span>
                </h4>
                <a
                  style={{ color: 'var(--red)', cursor: 'pointer', fontSize: 12 }}
                  onClick={() => onChange({ ...trade, modifiers: trade.modifiers.filter((_, k) => k !== i) })}
                >
                  remove
                </a>
              </div>
            </div>
            <div className="grid-3">
              {(mentry?.fields ?? []).map((f) => (
                <Field
                  key={f.name}
                  spec={f}
                  value={mod.params[f.name]}
                  onChange={(v) => setModifier(i, { ...mod, params: { ...mod.params, [f.name]: v } })}
                  assetNames={assetNames}
                />
              ))}
            </div>
          </div>
        )
      })}

      <div className="row" style={{ marginTop: 18 }}>
        <select className="sel" value="" onChange={(e) => e.target.value && addModifier(e.target.value)}>
          <option value="">+ Add modifier…</option>
          {Object.entries(registry.modifiers).map(([k, v]) => (
            <option key={k} value={k}>
              {v.label}
            </option>
          ))}
        </select>
        <div style={{ marginLeft: 'auto', fontSize: 12, color: 'var(--fg3)' }}>
          Chain: <span className="mono">{chain}</span>
        </div>
      </div>
    </div>
  )
}
