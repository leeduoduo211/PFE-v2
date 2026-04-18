/* Dashboard — single-page layout, no tabs. Everything at a glance. */
function Dashboard({ trades, runs, selectedId, onSelect }) {
  const chartRef = React.useRef(null);
  const miniRefs = React.useRef({});

  const weeks = React.useMemo(()=>Array.from({length:53}, (_,i)=>i),[]);
  const makeProfile = (scalePfe, scaleEpe, peakWeek=40) => {
    const pfe = weeks.map(w => scalePfe * Math.exp(-Math.pow((w-peakWeek)/18, 2)) * (w<48?1:Math.max(0,(52-w)/4)));
    const epe = weeks.map(w => scaleEpe * Math.exp(-Math.pow((w-peakWeek)/22, 2)) * (w<48?1:Math.max(0,(52-w)/4)));
    return { pfe, epe };
  };

  React.useEffect(()=>{
    if (!window.Plotly || !chartRef.current) return;
    const { pfe, epe } = makeProfile(3.9e6, 1.05e6, 40);
    window.Plotly.newPlot(chartRef.current, [
      {x:weeks, y:pfe, mode:'lines', name:'PFE 95%',
       line:{color:'#ef4444', width:2.5}, fill:'tozeroy', fillcolor:'rgba(239,68,68,0.10)'},
      {x:weeks, y:epe, mode:'lines', name:'EPE',
       line:{color:'#3b82f6', width:2}},
    ], {
      paper_bgcolor:'#ffffff', plot_bgcolor:'#ffffff',
      font:{family:'Inter,sans-serif', color:'#64748b', size:11},
      xaxis:{title:'Time (weeks)', gridcolor:'#f1f5f9', linecolor:'#e2e8f0',
             tickfont:{size:10,color:'#94a3b8'}, title_font:{size:11,color:'#64748b'}},
      yaxis:{title:'Exposure', gridcolor:'#f1f5f9', linecolor:'#e2e8f0', tickformat:',.0f',
             tickfont:{size:10,color:'#94a3b8'}, title_font:{size:11,color:'#64748b'}},
      margin:{l:70,r:20,t:16,b:44}, hovermode:'x unified',
      legend:{orientation:'h', yanchor:'bottom', y:1.02, xanchor:'right', x:1,
              bgcolor:'rgba(255,255,255,0)', font:{size:11,color:'#475569'}},
    }, {displayModeBar:false, responsive:true});
  }, []);

  // Per-trade sparklines
  React.useEffect(()=>{
    if (!window.Plotly) return;
    trades.forEach((t,i)=>{
      const el = miniRefs.current[t.id];
      if (!el) return;
      const peak = 32 + i*3;
      const sign = t.dir==='L' ? 1 : -1;
      const y = weeks.map(w => sign * Math.abs(t.mtm) * Math.exp(-Math.pow((w-peak)/16, 2)));
      window.Plotly.newPlot(el, [
        {x:weeks, y, mode:'lines', line:{color:sign>0?'#22c55e':'#ef4444', width:1.5},
         fill:'tozeroy', fillcolor:sign>0?'rgba(34,197,94,0.10)':'rgba(239,68,68,0.10)'},
      ], {
        paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
        xaxis:{visible:false}, yaxis:{visible:false, zeroline:true, zerolinecolor:'#e2e8f0'},
        margin:{l:0,r:0,t:0,b:0}, showlegend:false,
      }, {displayModeBar:false, staticPlot:true});
    });
  }, [trades]);

  const Icon = ({ path }) => (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="#64748b" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">{path}</svg>
  );

  const totalMtm = trades.reduce((s,t)=>s+t.mtm,0);
  const gross = trades.reduce((s,t)=>s+Math.abs(t.notional),0);

  return (
    <>
      <div className="between" style={{marginBottom:4}}>
        <div>
          <h1 className="page-title">Portfolio Credit Exposure</h1>
          <div className="page-sub">Run A · 5,000 × 2,000 · weekly · 52 steps · seed 42 · Apr 18, 2026 14:02 UTC</div>
        </div>
        <div className="row" style={{gap:6}}>
          <button className="btn btn-secondary btn-sm">Rerun</button>
          <button className="btn btn-secondary btn-sm">Export CSV</button>
          <button className="btn btn-primary btn-sm">Snapshot PDF</button>
        </div>
      </div>

      {/* KPI row */}
      <div className="kpi-grid" style={{marginTop:16}}>
        <div className="kpi kpi--red">
          <div className="kpi-label"><Icon path={<><path d="M1 11l3.5-4 2 2L10 4l3 5"/><circle cx="10" cy="4" r="1" fill="#ef4444" stroke="none"/></>}/>PEAK PFE</div>
          <div className="kpi-value">3,936,197</div>
          <div className="kpi-sub">95th percentile · week 40</div>
        </div>
        <div className="kpi kpi--accent">
          <div className="kpi-label"><Icon path={<path d="M7 1v12M2 4h10M3 7l-1.5 3h3zM11 7l-1.5 3h3z"/>}/>PEAK EPE</div>
          <div className="kpi-value">1,055,839</div>
          <div className="kpi-sub">EEPE 872,410</div>
        </div>
        <div className="kpi kpi--green">
          <div className="kpi-label"><Icon path={<path d="M7 1v12M9.5 3.5h-3a1.8 1.8 0 000 3.6h2a1.8 1.8 0 010 3.6h-3"/>}/>NET t=0 MtM</div>
          <div className="kpi-value">{totalMtm>=0?'+':'−'}{Math.abs(totalMtm).toLocaleString()}</div>
          <div className="kpi-sub">{trades.length} trades netted</div>
        </div>
        <div className="kpi kpi--amber">
          <div className="kpi-label"><Icon path={<><circle cx="7" cy="7" r="5.5"/><path d="M7 4v3l2 1.5"/></>}/>PEAK TIME</div>
          <div className="kpi-value">Week 40</div>
          <div className="kpi-sub">of 52 · T+0.77y</div>
        </div>
      </div>

      {/* Two-column: chart + run summary */}
      <div style={{display:'grid', gridTemplateColumns:'2fr 1fr', gap:16, marginBottom:16}}>
        <div className="card" style={{marginBottom:0}}>
          <div className="between" style={{marginBottom:4}}>
            <h3 style={{margin:0}}>Exposure profile</h3>
            <div className="row" style={{gap:10, fontSize:11, color:'var(--fg4)'}}>
              <span><span style={{display:'inline-block',width:8,height:8,background:'#ef4444',borderRadius:2,marginRight:4,verticalAlign:'middle'}}/>PFE 95%</span>
              <span><span style={{display:'inline-block',width:8,height:8,background:'#3b82f6',borderRadius:2,marginRight:4,verticalAlign:'middle'}}/>EPE</span>
            </div>
          </div>
          <div className="card-sub">PFE 95% (red) and EPE (blue) over the simulation horizon.</div>
          <div ref={chartRef} style={{height:260}} />
        </div>

        <div className="card" style={{marginBottom:0}}>
          <h3>Run A</h3>
          <div className="card-sub">Provenance + config snapshot.</div>
          <table className="pfe">
            <tbody>
              <tr><td style={{color:'var(--fg3)'}}>Outer paths</td><td className="num">5,000</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Inner paths</td><td className="num">2,000</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Grid</td><td className="num">weekly · 52</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Horizon</td><td className="num">1.00y</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Confidence</td><td className="num">0.9500</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Seed</td><td className="num">42</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Antithetic</td><td className="num" style={{color:'var(--green)'}}>● on</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Sobol</td><td className="num" style={{color:'var(--green)'}}>● on</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Runtime</td><td className="num">41.8s</td></tr>
              <tr><td style={{color:'var(--fg3)'}}>Gross notl.</td><td className="num">{(gross/1e6).toFixed(2)}M</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Per-trade grid with sparklines */}
      <div className="card">
        <div className="between" style={{marginBottom:4}}>
          <h3 style={{margin:0}}>Per-trade contribution</h3>
          <div className="row" style={{fontSize:11, color:'var(--fg4)'}}>
            Click a row to focus in the sidebar.
          </div>
        </div>
        <div className="card-sub">t=0 MtM, % of gross PFE, and MtM shape over time.</div>
        <table className="pfe">
          <thead>
            <tr>
              <th style={{width:'18%'}}>Trade</th>
              <th style={{width:'16%'}}>Category</th>
              <th className="num" style={{width:'14%'}}>t=0 MtM</th>
              <th className="num" style={{width:'12%'}}>Std. err.</th>
              <th className="num" style={{width:'12%'}}>PFE share</th>
              <th style={{width:'28%'}}>MtM shape</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t,i)=>{
              const share = [41,19,32,8][i] ?? 10;
              const cat = [
                {cls:'cat-eu', label:'EUROPEAN'},
                {cls:'cat-pd', label:'PATH-DEPENDENT'},
                {cls:'cat-pe', label:'PERIODIC'},
                {cls:'cat-ma', label:'MULTI-ASSET'},
              ][i] ?? {cls:'cat-eu', label:'EUROPEAN'};
              return (
                <tr key={t.id} style={{cursor:'pointer', background: t.id===selectedId?'var(--blue-dim)':'transparent'}} onClick={()=>onSelect(t.id)}>
                  <td>
                    <span className={'tag '+(t.dir==='L'?'tag-long':'tag-short')} style={{marginRight:6}}>{t.dir}</span>
                    <span style={{fontWeight:500}}>{t.id}</span>
                  </td>
                  <td><span className={'cat '+cat.cls}>{cat.label}</span></td>
                  <td className={'num '+(t.mtm>=0?'pos':'neg')}>{t.mtm>=0?'+':'−'}{Math.abs(t.mtm).toLocaleString()}</td>
                  <td className="num" style={{color:'var(--fg4)'}}>±{Math.round(Math.abs(t.mtm)*0.035).toLocaleString()}</td>
                  <td className="num" style={{color:'var(--fg2)'}}>{share}%</td>
                  <td><div ref={el=>{ if (el) miniRefs.current[t.id] = el; }} style={{height:34, width:'100%'}}/></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Recent runs strip */}
      <div className="card">
        <h3>Recent runs</h3>
        <div className="card-sub">Last 4 runs on this portfolio.</div>
        <table className="pfe">
          <thead>
            <tr>
              <th>ID</th><th>When</th><th>Config</th>
              <th className="num">Peak PFE</th><th className="num">Peak EPE</th><th className="num">Runtime</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr style={{background:'var(--blue-dim)'}}>
              <td><span style={{color:'var(--blue)'}}>●</span> Run A</td>
              <td style={{color:'var(--fg2)'}}>Apr 18 · 14:02</td>
              <td className="mono" style={{fontSize:11,color:'var(--fg3)'}}>5k×2k · weekly · sobol</td>
              <td className="num">3,936,197</td>
              <td className="num">1,055,839</td>
              <td className="num" style={{color:'var(--fg4)'}}>41.8s</td>
              <td style={{textAlign:'right'}}><span style={{fontSize:11,color:'var(--blue)'}}>current</span></td>
            </tr>
            <tr>
              <td><span style={{color:'var(--fg4)'}}>○</span> Run #07</td>
              <td style={{color:'var(--fg2)'}}>Apr 17 · 16:48</td>
              <td className="mono" style={{fontSize:11,color:'var(--fg3)'}}>5k×2k · weekly · antithetic</td>
              <td className="num">3,812,044</td>
              <td className="num">1,002,510</td>
              <td className="num" style={{color:'var(--fg4)'}}>39.2s</td>
              <td style={{textAlign:'right'}}><button className="btn btn-secondary btn-sm">Compare</button></td>
            </tr>
            <tr>
              <td><span style={{color:'var(--fg4)'}}>○</span> Run #06</td>
              <td style={{color:'var(--fg2)'}}>Apr 17 · 10:11</td>
              <td className="mono" style={{fontSize:11,color:'var(--fg3)'}}>2k×1k · weekly · baseline</td>
              <td className="num">3,840,210</td>
              <td className="num">1,018,330</td>
              <td className="num" style={{color:'var(--fg4)'}}>8.4s</td>
              <td style={{textAlign:'right'}}><button className="btn btn-secondary btn-sm">Compare</button></td>
            </tr>
            <tr>
              <td><span style={{color:'var(--fg4)'}}>○</span> Run #05</td>
              <td style={{color:'var(--fg2)'}}>Apr 16 · 18:30</td>
              <td className="mono" style={{fontSize:11,color:'var(--fg3)'}}>5k×2k · daily · sobol</td>
              <td className="num">4,102,883</td>
              <td className="num">1,144,220</td>
              <td className="num" style={{color:'var(--fg4)'}}>4m 12s</td>
              <td style={{textAlign:'right'}}><button className="btn btn-secondary btn-sm">Compare</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

Object.assign(window, { Dashboard });
