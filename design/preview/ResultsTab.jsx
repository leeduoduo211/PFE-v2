/* Results tab — KPIs, PFE/EPE chart, per-trade table */
function ResultsTab({ hasResults, onRun }) {
  const plotRef = React.useRef(null);

  React.useEffect(()=>{
    if (!hasResults || !plotRef.current || !window.Plotly) return;
    const weeks = Array.from({length:53}, (_,i)=>i);
    const pfe = weeks.map(w => 3.9e6 * Math.exp(-Math.pow((w-40)/18, 2)) * (w<48?1:Math.max(0,(52-w)/4)));
    const epe = weeks.map(w => 1.05e6 * Math.exp(-Math.pow((w-40)/22, 2)) * (w<48?1:Math.max(0,(52-w)/4)));
    const layout = {
      paper_bgcolor:'#ffffff', plot_bgcolor:'#ffffff',
      font:{family:'Inter,sans-serif', color:'#64748b', size:11},
      xaxis:{title:'Time (weeks)', gridcolor:'#f1f5f9', linecolor:'#e2e8f0',
             tickfont:{size:10,color:'#94a3b8'}, title_font:{size:11,color:'#64748b'}},
      yaxis:{title:'Exposure', gridcolor:'#f1f5f9', linecolor:'#e2e8f0',
             tickformat:',.0f',
             tickfont:{size:10,color:'#94a3b8'}, title_font:{size:11,color:'#64748b'}},
      margin:{l:70,r:20,t:30,b:50}, hovermode:'x unified',
      legend:{orientation:'h', yanchor:'bottom', y:1.02, xanchor:'right', x:1,
              bgcolor:'rgba(255,255,255,0)', font:{size:11,color:'#475569'}},
    };
    window.Plotly.newPlot(plotRef.current, [
      {x:weeks, y:pfe, mode:'lines', name:'PFE 95%',
       line:{color:'#ef4444', width:2.5}, fill:'tozeroy', fillcolor:'rgba(239,68,68,0.10)'},
      {x:weeks, y:epe, mode:'lines', name:'EPE',
       line:{color:'#3b82f6', width:2}},
    ], layout, {displayModeBar:false, responsive:true});
  }, [hasResults]);

  if (!hasResults) {
    return (
      <>
        <PageHeader title="Results" subtitle="Peak PFE, EPE, per-trade contribution, and exported snapshots." />
        <div className="card" style={{textAlign:'center', padding:'48px 20px'}}>
          <div style={{fontSize:28, color:'var(--fg4)', marginBottom:8}}>○</div>
          <div style={{fontSize:14, color:'var(--fg2)'}}>No results yet. Configure and run PFE in the Configuration tab.</div>
          <button className="btn btn-secondary btn-sm" style={{marginTop:14}} onClick={onRun}>Go to Configuration</button>
        </div>
      </>
    );
  }

  const Icon = ({ path }) => (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="#64748b" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">{path}</svg>
  );

  return (
    <>
      <PageHeader title="Results"
        subtitle="Run A · 5,000 outer × 2,000 inner · weekly · 52 steps · seed 42"
        right={<div className="row" style={{gap:6}}>
          <button className="btn btn-secondary btn-sm">Export CSV</button>
          <button className="btn btn-secondary btn-sm">Copy Python</button>
        </div>} />

      <div className="kpi-grid">
        <div className="kpi kpi--red">
          <div className="kpi-label"><Icon path={<><path d="M1 11l3.5-4 2 2L10 4l3 5"/><circle cx="10" cy="4" r="1" fill="#ef4444" stroke="none"/></>}/>PEAK PFE</div>
          <div className="kpi-value">3,936,197</div>
          <div className="kpi-sub">95th percentile</div>
        </div>
        <div className="kpi kpi--accent">
          <div className="kpi-label"><Icon path={<path d="M7 1v12M2 4h10M3 7l-1.5 3h3zM11 7l-1.5 3h3z"/>}/>PEAK EPE</div>
          <div className="kpi-value">1,055,839</div>
          <div className="kpi-sub">max of EPE profile</div>
        </div>
        <div className="kpi kpi--green">
          <div className="kpi-label"><Icon path={<path d="M7 1v12M9.5 3.5h-3a1.8 1.8 0 000 3.6h2a1.8 1.8 0 010 3.6h-3"/>}/>NET t=0 MtM</div>
          <div className="kpi-value">+45,036</div>
          <div className="kpi-sub">4 trades netted</div>
        </div>
        <div className="kpi kpi--amber">
          <div className="kpi-label"><Icon path={<><circle cx="7" cy="7" r="5.5"/><path d="M7 4v3l2 1.5"/></>}/>PEAK TIME</div>
          <div className="kpi-value">Week 40</div>
          <div className="kpi-sub">of 52 weeks</div>
        </div>
      </div>

      <div className="card">
        <h3>Exposure profile</h3>
        <div className="card-sub">PFE 95% (red) and EPE (blue) over the simulation horizon.</div>
        <div ref={plotRef} style={{height:320}} />
      </div>

      <div className="card">
        <h3>Per-trade t=0 MtM</h3>
        <table className="pfe">
          <thead><tr><th>Trade</th><th className="num">t=0 MtM</th><th className="num">% of Portfolio</th><th className="num">Std. err.</th></tr></thead>
          <tbody>
            <tr><td>TRD_001</td><td className="num pos">+12,450</td><td className="num" style={{color:'var(--fg4)'}}>27.6%</td><td className="num" style={{color:'var(--fg4)'}}>±421</td></tr>
            <tr><td>TRD_002</td><td className="num neg">−8,320</td><td className="num" style={{color:'var(--fg4)'}}>18.5%</td><td className="num" style={{color:'var(--fg4)'}}>±305</td></tr>
            <tr><td>AUTOCALL_01</td><td className="num pos">+42,110</td><td className="num" style={{color:'var(--fg4)'}}>93.5%</td><td className="num" style={{color:'var(--fg4)'}}>±1,204</td></tr>
            <tr><td>TARF_A</td><td className="num neg">−1,204</td><td className="num" style={{color:'var(--fg4)'}}>2.7%</td><td className="num" style={{color:'var(--fg4)'}}>±88</td></tr>
            <tr style={{fontWeight:600}}><td>Total</td><td className="num pos">+45,036</td><td className="num" style={{color:'var(--fg4)'}}>100%</td><td className="num" style={{color:'var(--fg4)'}}>±1,322</td></tr>
          </tbody>
        </table>
        <div style={{marginTop:10, fontSize:11, color:'var(--fg4)'}}>Tip: use Plotly's camera icon on the chart above to save a PNG.</div>
      </div>
    </>
  );
}

Object.assign(window, { ResultsTab });
