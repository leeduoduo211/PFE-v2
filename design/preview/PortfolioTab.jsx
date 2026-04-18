/* Portfolio tab — trade builder with modifier chain */
function PortfolioTab({ trades, selectedId, onSelect }) {
  const t = trades.find(x=>x.id===selectedId) || trades[0];
  return (
    <>
      <PageHeader title="Portfolio"
        subtitle="Add trades and stack modifiers. Each modifier wraps the previous payoff."
        right={<button className="btn btn-primary">+ Add trade</button>} />

      <div style={{display:'grid', gridTemplateColumns:'240px 1fr', gap:16}}>
        <div className="card" style={{padding:14}}>
          <div className="overline" style={{fontSize:10, color:'var(--fg4)', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600, marginBottom:8}}>Trades</div>
          {trades.map(x=>(
            <div key={x.id} className={'sb-item'+(x.id===t.id?' sel':'')} onClick={()=>onSelect(x.id)} style={{marginBottom:4}}>
              <span>{x.id}</span>
              <span className={'tag '+(x.dir==='L'?'tag-long':'tag-short')}>{x.dir}</span>
            </div>
          ))}
        </div>

        <div>
          <div className="card">
            <div className="between" style={{marginBottom:12}}>
              <div className="row">
                <span className="cat cat-pd">PATH-DEPENDENT</span>
                <h3 style={{margin:0}}>{t.id}</h3>
              </div>
              <div className="row" style={{gap:6}}>
                <button className="btn btn-secondary btn-sm">Clone</button>
                <button className="btn btn-secondary btn-sm" style={{color:'var(--red)'}}>Delete</button>
              </div>
            </div>

            <div className="group b-blue">
              <h4>Strike &amp; payoff</h4>
              <p>Core economic terms.</p>
            </div>
            <div className="grid-3">
              <div className="field"><label>Underlying</label>
                <select className="sel"><option>SPX</option><option>NDX</option></select>
              </div>
              <div className="field"><label>Strike</label><input className="inp" defaultValue="4450.00" /></div>
              <div className="field"><label>Direction</label>
                <select className="sel"><option>Long</option><option>Short</option></select>
              </div>
              <div className="field"><label>Notional</label><input className="inp" defaultValue="1,000,000" /></div>
              <div className="field"><label>Maturity (years)</label><input className="inp" defaultValue="1.50" /></div>
              <div className="field"><label>Observations</label><input className="inp" defaultValue="52" /></div>
            </div>

            <div className="group b-amber">
              <h4>Modifier: Knock-Out <span className="mg mg-barrier">BARRIER</span></h4>
              <p>Kills the trade when spot crosses the barrier.</p>
            </div>
            <div className="grid-3">
              <div className="field"><label>Barrier level</label><input className="inp" defaultValue="5340.00" /></div>
              <div className="field"><label>Direction</label>
                <select className="sel"><option>Up &amp; Out</option><option>Down &amp; Out</option></select>
              </div>
              <div className="field"><label>Rebate</label><input className="inp" defaultValue="0" /></div>
            </div>

            <div className="group b-green">
              <h4>Modifier: Payoff Cap <span className="mg mg-payoff">PAYOFF</span></h4>
              <p>Caps the maximum payout at the given level.</p>
            </div>
            <div className="grid-3">
              <div className="field"><label>Cap level</label><input className="inp" defaultValue="1,500,000" /></div>
            </div>

            <div className="row" style={{marginTop:18}}>
              <button className="btn btn-secondary btn-sm">+ Add modifier</button>
              <button className="btn btn-secondary btn-sm">- Remove last</button>
              <div style={{marginLeft:'auto', fontSize:12, color:'var(--fg3)'}}>
                Chain: <span className="mono">Payoff Cap → Knock-Out → VanillaCall</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

Object.assign(window, { PortfolioTab });
