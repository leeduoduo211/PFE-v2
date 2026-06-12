/** Wire types mirroring api/schemas.py and api/serializers.py. */

export interface MarketState {
  spots: number[]
  vols: number[]
  rates: number[]
  domestic_rate: number
  corr_matrix: number[][]
  asset_names: string[]
  asset_classes: string[]
}

export interface ModifierSpec {
  type: string
  params: Record<string, unknown>
}

export interface TradeSpec {
  trade_id: string
  instrument_type: string
  direction: 'long' | 'short'
  params: Record<string, unknown>
  modifiers: ModifierSpec[]
}

export interface ConfigState {
  n_outer?: number
  n_inner?: number
  confidence_level?: number
  grid_frequency?: 'daily' | 'weekly' | 'monthly'
  margined?: boolean
  mpor_days?: number
  backend?: string
  n_workers?: number
  seed?: number
  antithetic?: boolean
}

/** Registry field spec — same schema that drives the Streamlit forms. */
export interface FieldSpec {
  name: string
  label: string
  type:
    | 'float'
    | 'int'
    | 'select'
    | 'float_list'
    | 'select_list'
    | 'asset_select'
    | 'asset_select_optional'
    | 'schedule'
  default?: unknown
  choices?: string[]
  help?: string
}

export interface InstrumentEntry {
  label: string
  category: string
  n_assets: number | string // int or "2-5"
  fields: FieldSpec[]
}

export interface ModifierEntry {
  label: string
  group?: string
  category?: string
  fields: FieldSpec[]
}

export interface RegistryPayload {
  instruments: Record<string, InstrumentEntry>
  modifiers: Record<string, ModifierEntry>
}

export type RunStatus = 'queued' | 'running' | 'completed' | 'failed'

export interface RunSummary {
  run_id: string
  label: string | null
  status: RunStatus
  progress: number
  error: string | null
  submitted_at: number
  started_at: number | null
  finished_at: number | null
  peak_pfe: number | null
  computation_time: number | null
}

export interface ResultPayload {
  time_points: number[]
  time_points_in_periods: number[]
  period_label: string
  pfe_curve: number[]
  epe_curve: number[]
  unmargined_pfe_curve: number[] | null
  unmargined_epe_curve: number[] | null
  peak_pfe: number
  eepe: number
  computation_time: number
  config: Required<ConfigState>
  per_trade_t0_mtm?: number[]
  mtm_matrix?: number[][]
}
