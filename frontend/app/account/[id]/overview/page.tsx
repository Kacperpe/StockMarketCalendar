const cards = [
  ["Balance", "12 450.22"],
  ["Equity", "12 396.08"],
  ["Today PnL", "+142.11"],
  ["Week PnL", "-88.43"],
  ["Max DD (30d)", "4.6%"],
  ["Win rate", "57.8%"]
] as const;

export default async function OverviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <main>
      <h1 className="pageTitle">Overview konta #{id}</h1>
      <p className="subtitle">Kafelki KPI + equity curve + ostatnie transakcje.</p>

      <div className="grid cards">
        {cards.map(([label, value]) => (
          <section key={label} className="card">
            <div className="label">{label}</div>
            <div className="value">{value}</div>
          </section>
        ))}
      </div>

      <section className="card" style={{ marginTop: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 12 }}>
          <h2 className="sectionTitle">Equity Curve</h2>
          <div className="rangeSwitch">
            <span>7d</span>
            <span className="active">30d</span>
            <span>90d</span>
            <span>all</span>
          </div>
        </div>
        <div className="chartPlaceholder">Wykres (API: /equity-curve)</div>
      </section>

      <section style={{ marginTop: 16 }}>
        <h2 className="sectionTitle">Ostatnie transakcje</h2>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Volume</th>
                <th>Open</th>
                <th>Close</th>
                <th>PnL</th>
                <th>Fees</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>EURUSD</td>
                <td>buy</td>
                <td>0.50</td>
                <td>2026-02-25 09:20</td>
                <td>2026-02-25 10:03</td>
                <td style={{ color: "var(--success)" }}>+85.40</td>
                <td>-4.20</td>
              </tr>
              <tr>
                <td>NAS100</td>
                <td>sell</td>
                <td>1.00</td>
                <td>2026-02-25 12:11</td>
                <td>2026-02-25 12:44</td>
                <td style={{ color: "var(--danger)" }}>-53.10</td>
                <td>-2.10</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

