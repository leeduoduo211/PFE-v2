/* Market Data tab — assets, spot, vol, correlation */
function MarketDataTab() {
  const assets = [
    { t:'SPX',  spot:4450.12, vol:0.18 },
    { t:'NDX',  spot:15420.5, vol:0.22 },
    { t:'EURUSD', spot:1.0852, vol:0.09 },
    { t:'BRENT', spot:78.42,   vol:0.34 },
  ];
  const corr = [
    [1.00, 0.85, -0.12, 0.28],
    [0.85, 1.00, -0.05, 0.22],
    [-0.12,-0.05, 1.00, -0.18],
    [0.28, 0.22, -0.18, 1.00],
  ];
  return (
    <>
      <PageHeader title="Market Data"
        subtitle="Define assets, spot prices, volatilities, and correlation structure."
        right={<button className="btn btn-secondary btn-sm">Load preset: G10 equity</button>} />

      <div className="card">
        <h3>Assets</h3>
        <div className="card-sub">Tickers are free-form — match your pricer's lookup.</div>
        <table className="pfe">
          <thead><tr><th>Ticker</th><th className="num">Spot</th><th className="num">Vol (ann.)</th><th className="num">Drift</th><th></th></tr></thead>
          <tbody>
            {assets.map((a,i)=>(
              <tr key={a.t}>
                <td style={{fontWeight:500}}>{a.t}</td>
                <td className="num">{a.spot.toLocaleString()}</td>
                <td className="num">{(a.vol*100).toFixed(1)}%</td>
                <td className="num" style={{color:'var(--fg4)'}}>0.0%</td>
                <td style={{textAlign:'right'}}><button className="btn btn-secondary btn-sm">Edit</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row" style={{marginTop:12}}>
          <button className="btn btn-secondary btn-sm">+ Add asset</button>
          <small style={{color:'var(--fg4)'}}>4 of 10 asset cap.</small>
        </div>
      </div>

      <div className="card">
        <h3>Correlation matrix</h3>
        <div className="card-sub">Must be positive semi-definite. Validated on save.</div>
        <table className="pfe" style={{maxWidth:420}}>
          <thead><tr><th></th>{assets.map(a=><th key={a.t} className="num">{a.t}</th>)}</tr></thead>
          <tbody>
            {corr.map((row,i)=>(
              <tr key={i}>
                <td style={{fontWeight:500}}>{assets[i].t}</td>
                {row.map((v,j)=>(
                  <td key={j} className="num" style={{
                    color: i===j?'var(--fg4)':(v>0?'var(--fg1)':'var(--red)'),
                    background: i===j?'transparent':`rgba(${v>0?'59,130,246':'239,68,68'},${Math.abs(v)*0.12})`
                  }}>{v.toFixed(2)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{marginTop:10, fontSize:12, color:'var(--fg3)'}}>PSD check: <span style={{color:'var(--green)'}}>● passes</span> (min eigenvalue 0.054)</div>
      </div>
    </>
  );
}

Object.assign(window, { MarketDataTab });
