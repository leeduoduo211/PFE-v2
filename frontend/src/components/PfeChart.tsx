import Plotly from 'plotly.js-dist-min'
import { useEffect, useRef } from 'react'
import type { ResultPayload } from '../api/types'

/** PFE/EPE exposure profile — layout matches the pfe_light Plotly template. */
export function PfeChart({ result }: { result: ResultPayload }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const x = result.time_points_in_periods
    void Plotly.newPlot(
      el,
      [
        {
          x,
          y: result.pfe_curve,
          mode: 'lines',
          name: `PFE ${Math.round(result.config.confidence_level * 100)}%`,
          line: { color: '#ef4444', width: 2.5 },
          fill: 'tozeroy',
          fillcolor: 'rgba(239,68,68,0.10)',
        },
        {
          x,
          y: result.epe_curve,
          mode: 'lines',
          name: 'EPE',
          line: { color: '#3b82f6', width: 2 },
        },
      ],
      {
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#ffffff',
        font: { family: 'Inter,sans-serif', color: '#64748b', size: 11 },
        xaxis: {
          title: { text: `Time (${result.period_label})`, font: { size: 11, color: '#64748b' } },
          gridcolor: '#f1f5f9',
          linecolor: '#e2e8f0',
          tickfont: { size: 10, color: '#94a3b8' },
        },
        yaxis: {
          title: { text: 'Exposure', font: { size: 11, color: '#64748b' } },
          gridcolor: '#f1f5f9',
          linecolor: '#e2e8f0',
          tickformat: ',.0f',
          tickfont: { size: 10, color: '#94a3b8' },
        },
        margin: { l: 70, r: 20, t: 30, b: 50 },
        hovermode: 'x unified',
        legend: {
          orientation: 'h',
          yanchor: 'bottom',
          y: 1.02,
          xanchor: 'right',
          x: 1,
          bgcolor: 'rgba(255,255,255,0)',
          font: { size: 11, color: '#475569' },
        },
      },
      { displayModeBar: false, responsive: true },
    )
    return () => Plotly.purge(el)
  }, [result])

  return <div ref={ref} style={{ height: 320 }} />
}
