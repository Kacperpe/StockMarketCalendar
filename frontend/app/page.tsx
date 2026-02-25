import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1 className="pageTitle">Trading Monitor MVP</h1>
      <p className="subtitle">
        Szkielet UI pod logowanie, konta, overview, dzienny PnL i historię trade&apos;ów.
      </p>
      <div className="actions">
        <Link className="button primary" href="/accounts">Przejdź do kont</Link>
        <Link className="button" href="/account/1/overview">Zobacz konto (mock)</Link>
      </div>
      <div className="grid cards">
        <section className="card">
          <div className="label">Backend API</div>
          <div className="value">FastAPI</div>
        </section>
        <section className="card">
          <div className="label">Data</div>
          <div className="value">PostgreSQL + Redis</div>
        </section>
        <section className="card">
          <div className="label">Integracje</div>
          <div className="value">MT5 ingest / cTrader OAuth</div>
        </section>
      </div>
    </main>
  );
}

