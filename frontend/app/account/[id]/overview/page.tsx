import AdvancedStatisticsPanel from "../../../../components/AdvancedStatisticsPanel";

type StatusBadge = {
  label: string;
  tone: "ok" | "muted";
};

type AccountFact = {
  label: string;
  value: string;
  meta?: string;
  tone?: "up";
};

type PeriodRow = {
  label: string;
  gain: string;
  gainDiff: string;
  profit: string;
  profitDiff: string;
  pips: string;
  pipsDiff: string;
  win: string;
  winDiff: string;
  trades: string;
  tradesDiff: string;
  lots: string;
  lotsDiff: string;
};

const statusBadges: StatusBadge[] = [
  { label: "Track record", tone: "ok" },
  { label: "Trading privileges", tone: "ok" },
  { label: "Live update", tone: "muted" },
  { label: "Cashback", tone: "muted" }
] ;

const accountFacts: AccountFact[] = [
  { label: "Gain", value: "+16.40%", tone: "up" },
  { label: "Abs. Gain", value: "+16.40%", tone: "up" },
  { label: "Daily", value: "7.89%" },
  { label: "Monthly", value: "16.40%" },
  { label: "Drawdown", value: "25.38%" },
  { label: "Balance", value: "$11,640.03" },
  { label: "Equity", value: "$11,640.03", meta: "(100.00%)" },
  { label: "Highest", value: "$11,640.03", meta: "(Feb 25)" },
  { label: "Profit", value: "$1,640.03", tone: "up" },
  { label: "Interest", value: "$0.00" },
  { label: "Deposits", value: "$10,000.00" },
  { label: "Withdrawals", value: "$0.00" },
  { label: "Updated", value: "1 hour ago" },
  { label: "Tracking", value: "0" }
] ;

const periods: PeriodRow[] = [
  {
    label: "Today",
    gain: "+3.59%",
    gainDiff: "(-2.47%)",
    profit: "$403.11",
    profitDiff: "(-$238.39)",
    pips: "-730.0",
    pipsDiff: "(-1,017.0)",
    win: "33%",
    winDiff: "(-33%)",
    trades: "3",
    tradesDiff: "(0)",
    lots: "8.03",
    lotsDiff: "(+1.16)"
  },
  {
    label: "This Week",
    gain: "+16.40%",
    gainDiff: "(-)",
    profit: "$1,640.03",
    profitDiff: "(-)",
    pips: "+252.0",
    pipsDiff: "(-)",
    win: "50%",
    winDiff: "(-)",
    trades: "8",
    tradesDiff: "(-)",
    lots: "15.75",
    lotsDiff: "(-)"
  },
  {
    label: "This Month",
    gain: "+16.40%",
    gainDiff: "(-)",
    profit: "$1,640.03",
    profitDiff: "(-)",
    pips: "+252.0",
    pipsDiff: "(-)",
    win: "50%",
    winDiff: "(-)",
    trades: "8",
    tradesDiff: "(-)",
    lots: "15.75",
    lotsDiff: "(-)"
  },
  {
    label: "This Year",
    gain: "+16.40%",
    gainDiff: "(-)",
    profit: "$1,640.03",
    profitDiff: "(-)",
    pips: "+252.0",
    pipsDiff: "(-)",
    win: "50%",
    winDiff: "(-)",
    trades: "8",
    tradesDiff: "(-)",
    lots: "15.75",
    lotsDiff: "(-)"
  }
] ;

export function generateStaticParams() {
  return [{ id: "1" }];
}

export default async function OverviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <main className="mf-page">
      <header className="mf-topbar">
        <div>
          <h1 className="mf-title">Trading Account Overview #{id}</h1>
          <p className="mf-subtitle">Widok inspirowany panelem statystyk / growth chart z Twojego zrzutu.</p>
        </div>
        <button className="mf-subscribe" type="button">Subscribe</button>
      </header>

      <section className="mf-statusRow" aria-label="Account status badges">
        {statusBadges.map((badge) => (
          <div key={badge.label} className={`mf-statusBadge ${badge.tone === "ok" ? "is-ok" : "is-muted"}`}>
            <span className="mf-statusIcon" aria-hidden="true">
              {badge.tone === "ok" ? "v" : "!"}
            </span>
            <span>{badge.label}</span>
          </div>
        ))}
      </section>

      <section className="mf-panel">
        <div className="mf-mainTabs" role="tablist" aria-label="Overview sections">
          <button className="mf-tab" type="button">Info</button>
          <button className="mf-tab" type="button">Stats</button>
          <button className="mf-tab is-active" type="button" aria-selected="true">General</button>
        </div>

        <div className="mf-grid">
          <aside className="mf-statsCard">
            <dl className="mf-facts">
              {accountFacts.map((fact) => (
                <div key={fact.label} className="mf-factRow">
                  <dt>{fact.label}:</dt>
                  <dd className={fact.tone === "up" ? "is-up" : undefined}>
                    {fact.meta ? <span className="mf-meta">{fact.meta} </span> : null}
                    {fact.value}
                  </dd>
                </div>
              ))}
            </dl>
          </aside>

          <section className="mf-chartCard" aria-label="Growth chart">
            <div className="mf-chartTabs" role="tablist" aria-label="Chart types">
              <button className="mf-tab is-active" type="button">Chart</button>
              <button className="mf-tab" type="button">Growth</button>
              <button className="mf-tab" type="button">Balance</button>
              <button className="mf-tab" type="button">Profit</button>
              <button className="mf-tab" type="button">Drawdown</button>
              <button className="mf-tab" type="button">
                Margin <span className="mf-newTag">New</span>
              </button>
            </div>

            <div className="mf-chartWrap">
              <div className="mf-yAxis">
                {["20%", "16%", "12%", "8%", "4%"].map((tick) => (
                  <span key={tick}>{tick}</span>
                ))}
              </div>

              <div className="mf-chartArea">
                <div className="mf-gridLines" aria-hidden="true" />
                <div className="mf-bar mf-bar-1" aria-hidden="true" />
                <div className="mf-bar mf-bar-2" aria-hidden="true" />
                <div className="mf-bar mf-bar-3" aria-hidden="true" />

                <svg className="mf-lineSvg" viewBox="0 0 100 60" preserveAspectRatio="none" aria-hidden="true">
                  <polyline
                    fill="none"
                    stroke="#f14747"
                    strokeWidth="1.2"
                    points="10,48 55,28 92,18"
                  />
                  <circle cx="55" cy="28" r="1.7" fill="#fff" stroke="#f14747" strokeWidth="1" />
                </svg>

                <div className="mf-tooltip" style={{ left: "55%", top: "18%" }}>
                  <div>Growth</div>
                  <div>Feb 24, &apos;26</div>
                  <strong>12.37%</strong>
                </div>

                <div className="mf-xLabels" aria-hidden="true">
                  <span>Feb 23, &apos;26</span>
                  <span>Feb 24, &apos;26</span>
                  <span>Feb 25, &apos;26</span>
                </div>
              </div>
            </div>

            <div className="mf-legend" aria-label="Chart legend">
              <span><i className="mf-dot mf-dot-yellow" /> Equity</span>
              <span><i className="mf-dot mf-dot-red" /> Growth</span>
              <span><i className="mf-dot mf-dot-green" /> Deposit</span>
            </div>
          </section>
        </div>
      </section>

      <section className="mf-lowerPanel">
        <div className="mf-mainTabs" role="tablist" aria-label="Bottom analytics sections">
          <button className="mf-tab is-active" type="button">Trading</button>
          <button className="mf-tab" type="button">Periods</button>
          <button className="mf-tab" type="button">Goals</button>
          <button className="mf-tab" type="button">Browser</button>
        </div>

        <div className="mf-tableWrap">
          <table className="mf-table">
            <thead>
              <tr>
                <th />
                <th>Gain (Difference)</th>
                <th>Profit (Difference)</th>
                <th>Pips (Difference)</th>
                <th>Win% (Difference)</th>
                <th>Trades (Difference)</th>
                <th>Lots (Difference)</th>
              </tr>
            </thead>
            <tbody>
              {periods.map((row) => (
                <tr key={row.label}>
                  <td>{row.label}</td>
                  <td><span className="is-up">{row.gain}</span> <span className="mf-diff">{row.gainDiff}</span></td>
                  <td><span className="is-up">{row.profit}</span> <span className="mf-diff">{row.profitDiff}</span></td>
                  <td className={row.pips.startsWith("+") ? "is-up" : "is-down"}>{row.pips} <span className="mf-diff">{row.pipsDiff}</span></td>
                  <td>{row.win} <span className="mf-diff">{row.winDiff}</span></td>
                  <td>{row.trades} <span className="mf-diff">{row.tradesDiff}</span></td>
                  <td>{row.lots} <span className="mf-diff">{row.lotsDiff}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <AdvancedStatisticsPanel />
    </main>
  );
}

