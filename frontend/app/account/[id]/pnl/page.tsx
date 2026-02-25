export default async function PnlPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <main>
      <h1 className="pageTitle">Dzienny PnL • konto #{id}</h1>
      <p className="subtitle">MVP: tabela dni -> PnL z możliwością wejścia w dzień i listę trade&apos;ów.</p>
      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Dzień</th>
              <th>Realized PnL</th>
              <th>Commissions</th>
              <th>Swap</th>
              <th>Fees</th>
              <th>Net PnL</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>2026-02-25</td>
              <td>+148.20</td>
              <td>-5.10</td>
              <td>0.00</td>
              <td>-1.00</td>
              <td style={{ color: "var(--success)" }}>+142.10</td>
            </tr>
            <tr>
              <td>2026-02-24</td>
              <td>-91.00</td>
              <td>-4.00</td>
              <td>-0.50</td>
              <td>0.00</td>
              <td style={{ color: "var(--danger)" }}>-95.50</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  );
}

