/** Typed fetch client for the PFE-v2 REST API (proxied under /api). */

import type {
  ConfigState,
  MarketState,
  RegistryPayload,
  ResultPayload,
  RunSummary,
  TradeSpec,
} from './types'

const BASE = '/api'

export class ApiError extends Error {
  status: number
  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  const body = await resp.json().catch(() => ({}))
  if (!resp.ok) {
    const detail =
      typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail ?? body)
    throw new ApiError(resp.status, detail)
  }
  return body as T
}

export interface RunRequestBody {
  market: MarketState
  portfolio: TradeSpec[]
  config: ConfigState
  label?: string | null
}

export const api = {
  registry: () => request<RegistryPayload>('/registry'),

  t0Mtm: (body: Omit<RunRequestBody, 'label'>) =>
    request<{ per_trade_t0_mtm: number[] }>('/t0-mtm', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  submitRun: (body: RunRequestBody) =>
    request<RunSummary>('/runs', { method: 'POST', body: JSON.stringify(body) }),

  listRuns: () => request<RunSummary[]>('/runs'),

  runStatus: (runId: string) => request<RunSummary>(`/runs/${runId}`),

  runResult: (runId: string) => request<ResultPayload>(`/runs/${runId}/result`),
}
