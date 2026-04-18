/* Sidebar — brand + portfolio summary + trade list + run history */
const { useState } = React;

function Sidebar({ trades, selectedId, onSelect, runs }) {
  const gross = trades.reduce((s,t)=>s+Math.abs(t.notional),0);
  const net   = trades.reduce((s,t)=>s+(t.dir==='L'?t.notional:-t.notional),0);
  const maxMat = Math.max(...trades.map(t=>t.maturity),0);

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
        <div><span>Gross notl.</span><span className="mono">{(gross/1e6).toFixed(2)}M</span></div>
        <div><span>Net notl.</span><span className="mono">{net>=0?'+':''}{(net/1e6).toFixed(2)}M</span></div>
        <div><span>Max maturity</span><span className="mono">{maxMat.toFixed(2)}y</span></div>
      </div>
      {trades.map(t=>(
        <div key={t.id} className={'sb-item'+(t.id===selectedId?' sel':'')} onClick={()=>onSelect(t.id)}>
          <span style={{color:'var(--fg1)',fontWeight:500}}>{t.id}</span>
          <span className="row" style={{gap:6}}>
            <span className={'tag '+(t.dir==='L'?'tag-long':'tag-short')}>{t.dir}</span>
            <span className="sb-num">{t.mtm>=0?'+':'−'}{Math.abs(t.mtm).toLocaleString()}</span>
          </span>
        </div>
      ))}

      <div className="sb-overline">Run history</div>
      {runs.map(r=>(
        <div key={r.id} className="sb-item">
          <span>{r.label}</span>
          <span className="sb-num">{r.peak}</span>
        </div>
      ))}

      <div className="sb-overline">Save &amp; load</div>
      <div className="row" style={{gap:6}}>
        <button className="btn btn-secondary btn-sm">Save</button>
        <button className="btn btn-secondary btn-sm">Load</button>
      </div>
    </aside>
  );
}

Object.assign(window, { Sidebar });
