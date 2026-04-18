/* Configuration tab — simulation params */
function ConfigTab({ onRun }) {
  return (
    <>
      <PageHeader title="Configuration"
        subtitle="Simulation parameters for the nested Monte Carlo run." />

      <div className="card">
        <h3>Sampling</h3>
        <div className="grid-3">
          <div className="field"><label>Outer paths</label><input className="inp" defaultValue="5000" />
            <small>World scenarios (market futures).</small></div>
          <div className="field"><label>Inner paths</label><input className="inp" defaultValue="2000" />
            <small>Per-state pricer revaluations.</small></div>
          <div className="field"><label>Seed</label><input className="inp" defaultValue="42" />
            <small>Reproducibility.</small></div>
          <div className="field"><label>Grid frequency</label>
            <select className="sel"><option>weekly</option><option>daily</option><option>monthly</option></select>
            <small>Exposure sampling granularity.</small></div>
          <div className="field"><label>Confidence</label><input className="inp" defaultValue="0.9500" />
            <small>PFE quantile level.</small></div>
          <div className="field"><label>Horizon (yrs)</label><input className="inp" defaultValue="1.00" />
            <small>Max lookout.</small></div>
        </div>
      </div>

      <div className="card">
        <h3>Variance reduction</h3>
        <div className="grid-2">
          <label className="row" style={{fontSize:13, color:'var(--fg2)', cursor:'pointer'}}>
            <input type="checkbox" defaultChecked /> Antithetic variates
            <span style={{marginLeft:'auto', fontSize:11, color:'var(--fg4)'}}>pair Z and −Z</span>
          </label>
          <label className="row" style={{fontSize:13, color:'var(--fg2)', cursor:'pointer'}}>
            <input type="checkbox" /> Control variates
            <span style={{marginLeft:'auto', fontSize:11, color:'var(--fg4)'}}>Black-Scholes baseline</span>
          </label>
          <label className="row" style={{fontSize:13, color:'var(--fg2)', cursor:'pointer'}}>
            <input type="checkbox" defaultChecked /> Sobol quasi-random
            <span style={{marginLeft:'auto', fontSize:11, color:'var(--fg4)'}}>low-discrepancy outer</span>
          </label>
          <label className="row" style={{fontSize:13, color:'var(--fg2)', cursor:'pointer'}}>
            <input type="checkbox" /> Stratified sampling
            <span style={{marginLeft:'auto', fontSize:11, color:'var(--fg4)'}}>per-quantile bucketing</span>
          </label>
        </div>
      </div>

      <div className="banner">
        <div>Estimated runtime: <span className="mono">~42s</span> <span style={{color:'var(--fg4)'}}>(5,000 × 52 × 2,000 × 3 trades)</span></div>
        <button className="btn btn-primary" onClick={onRun}>Run PFE →</button>
      </div>
    </>
  );
}

Object.assign(window, { ConfigTab });
