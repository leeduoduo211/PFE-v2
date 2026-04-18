/* Step tabs + page header */
function StepTabs({ step, setStep, tradeCount }) {
  const steps = [
    { n:1, label:'Market Data',   state:'done' },
    { n:2, label:`Portfolio (${tradeCount})`, state:'done' },
    { n:3, label:'Configuration', state:'next' },
    { n:4, label:'Results',       state:'pending' },
  ];
  const glyph = (s,active) => {
    if (active) return '●';
    if (s==='done')    return '●';
    if (s==='next')    return '▸';
    return '○';
  };
  return (
    <div className="tabs">
      {steps.map(s=>(
        <div key={s.n} className={'tab'+(step===s.n?' active':'')} onClick={()=>setStep(s.n)}>
          <span style={{marginRight:6, color: step===s.n || s.state==='done' ? 'var(--blue)' : 'var(--fg4)'}}>{glyph(s.state, step===s.n)}</span>
          {s.n}. {s.label}
        </div>
      ))}
    </div>
  );
}

function PageHeader({ title, subtitle, right }) {
  return (
    <div className="between" style={{marginBottom:4}}>
      <div>
        <h1 className="page-title">{title}</h1>
        <div className="page-sub">{subtitle}</div>
      </div>
      {right}
    </div>
  );
}

Object.assign(window, { StepTabs, PageHeader });
