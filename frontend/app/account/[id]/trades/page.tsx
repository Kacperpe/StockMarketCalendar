export function generateStaticParams() {
  return [{ id: "1" }];
}

export default async function TradesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <main>
      <h1 className="pageTitle">Trade&apos;y • konto #{id}</h1>
      <p className="subtitle">Tabela trade&apos;ów + filtry (data, symbol, pnl sign, typ) + eksport CSV.</p>

      <div className="filters">
        <input className="field" type="date" />
        <input className="field" type="date" />
        <input className="field" placeholder="Symbol" />
        <select className="field" defaultValue="">
          <option value="">PnL +/-</option>
          <option value="positive">Dodatni</option>
          <option value="negative">Ujemny</option>
        </select>
        <select className="field" defaultValue="">
          <option value="">Typ</option>
          <option value="deal">Deal</option>
          <option value="order">Order</option>
        </select>
        <button className="button">Eksport CSV</button>
      </div>

      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Side</th>
              <th>Volume</th>
              <th>Open/Close</th>
              <th>PnL</th>
              <th>Fees</th>
              <th>Comment</th>
              <th>Magic</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>XAUUSD</td>
              <td>buy</td>
              <td>0.10</td>
              <td>09:00 / 09:25</td>
              <td>+36.40</td>
              <td>-1.20</td>
              <td>breakout</td>
              <td>1001</td>
            </tr>
            <tr>
              <td>EURUSD</td>
              <td>sell</td>
              <td>1.00</td>
              <td>11:14 / 11:41</td>
              <td>-27.00</td>
              <td>-2.30</td>
              <td>scalp</td>
              <td>1001</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  );
}
