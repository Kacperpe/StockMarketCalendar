export default function AccountsPage() {
  return (
    <main>
      <h1 className="pageTitle">Konta</h1>
      <p className="subtitle">Lista kont + akcje dodawania MT5 / cTrader.</p>
      <div className="actions">
        <button className="button primary">Dodaj MT5</button>
        <button className="button">Dodaj cTrader</button>
      </div>
      <div className="grid">
        <section className="card">
          <div className="label">Konto</div>
          <div className="value" style={{ fontSize: 18 }}>FTMO MT5 Main</div>
          <p className="subtitle" style={{ marginBottom: 0 }}>Provider: MT5 • Currency: USD • Status: active</p>
        </section>
        <section className="card">
          <div className="label">Konto</div>
          <div className="value" style={{ fontSize: 18 }}>cTrader Demo</div>
          <p className="subtitle" style={{ marginBottom: 0 }}>Provider: CTrader • Currency: EUR • Status: new</p>
        </section>
      </div>
    </main>
  );
}

