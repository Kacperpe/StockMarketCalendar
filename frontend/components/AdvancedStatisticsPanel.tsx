"use client";

import { useState } from "react";

type AdvancedTab =
  | "advanced"
  | "trades"
  | "summary"
  | "hourly"
  | "daily"
  | "risk"
  | "duration"
  | "mae";

type TradeSummaryRow = {
  currency: string;
  longTrades: number;
  longPips: number;
  longProfit: number;
  shortTrades: number;
  shortPips: number;
  shortProfit: number;
  totalTrades: number;
  totalPips: number;
  totalProfit: number;
  wonPct: string;
  lostPct: string;
};

type HourBucket = {
  hour: string;
  winners: number;
  losers: number;
};

type RiskColumn = {
  lossSize: string;
  probability: string;
  streak: string;
};

const tabs: Array<{ id: AdvancedTab; label: string }> = [
  { id: "advanced", label: "Advanced Statistics" },
  { id: "trades", label: "Trades" },
  { id: "summary", label: "Summary" },
  { id: "hourly", label: "Hourly" },
  { id: "daily", label: "Daily" },
  { id: "risk", label: "Risk of Ruin" },
  { id: "duration", label: "Duration" },
  { id: "mae", label: "MAE/MFE" }
];

const advancedRows = [
  ["Trades", "8", "Longs Won", "(3/6) 50%", "Profit Factor", "1.44"],
  ["Profitability", "60%", "Shorts Won", "(1/2) 50%", "Standard Deviation", "$1,596.978"],
  ["Pips", "252.0", "Best Trade ($)", "(Feb 25) 3,255.10", "Sharpe Ratio", "0.18"],
  ["Average Win", "529.25 pips / $1,332.34", "Worst Trade ($)", "(Feb 25) -1,918.20", "Z-Score (Probability)", "1.15 (74.98%)"],
  ["Average Loss", "-466.25 pips / -$922.33", "Best Trade (Pips)", "(Feb 25) 757.0", "Expectancy", "31.5 Pips / $205.00"],
  ["Lots", "15.75", "Worst Trade (Pips)", "(Feb 25) -834.0", "AHPR", "3.12%"],
  ["Commissions", "$0.00", "Avg. Trade Length", "4m", "GHPR", "1.92%"]
] as const;

const tradeSummaryRows: TradeSummaryRow[] = [
  {
    currency: "XAUUSD",
    longTrades: 6,
    longPips: -443,
    longProfit: 1044.61,
    shortTrades: 2,
    shortPips: 695,
    shortProfit: 595.42,
    totalTrades: 8,
    totalPips: 252,
    totalProfit: 1640.03,
    wonPct: "4 (50%)",
    lostPct: "4 (50%)"
  }
];

const hourlyBuckets: HourBucket[] = [
  { hour: "14", winners: 2, losers: 2 },
  { hour: "15", winners: 1, losers: 0 },
  { hour: "16", winners: 1, losers: 2 }
];

const dailyHeat = [
  ["Mon", 1, 0, 0, 2, 1],
  ["Tue", 0, 1, 1, 0, 2],
  ["Wed", 0, 0, 3, 1, 0],
  ["Thu", 2, 0, 1, 0, 0],
  ["Fri", 1, 2, 0, 1, 1]
] as const;

const riskColumns: RiskColumn[] = [
  { lossSize: "100%", probability: "<0.01%", streak: "13" },
  { lossSize: "90%", probability: "1.82%", streak: "11" },
  { lossSize: "80%", probability: "6.08%", streak: "10" },
  { lossSize: "70%", probability: "12.31%", streak: "9" },
  { lossSize: "60%", probability: "20.31%", streak: "8" },
  { lossSize: "50%", probability: "29.94%", streak: "6" },
  { lossSize: "40%", probability: "41.12%", streak: "5" },
  { lossSize: "30%", probability: "53.77%", streak: "4" },
  { lossSize: "20%", probability: "67.83%", streak: "3" },
  { lossSize: "10%", probability: "83.25%", streak: "1" }
];

function fmtMoney(value: number): string {
  return new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value);
}

function ProfitabilityBar() {
  return (
    <div className="ast-profitBar" aria-label="Profitability 60%">
      <span className="ast-profitBarWin" style={{ width: "60%" }} />
      <span className="ast-profitBarLoss" style={{ width: "40%" }} />
    </div>
  );
}

function AdvancedGrid() {
  return (
    <div className="ast-kvGrid">
      {advancedRows.map((row) => (
        <div key={row[0]} className="ast-kvRow">
          <div className="ast-kvCell ast-kLabel">{row[0]}:</div>
          <div className="ast-kvCell ast-kValue">
            {row[0] === "Profitability" ? <ProfitabilityBar /> : row[1]}
          </div>
          <div className="ast-kvCell ast-kLabel">{row[2]}:</div>
          <div className="ast-kvCell ast-kValue">{row[3]}</div>
          <div className="ast-kvCell ast-kLabel">{row[4]}:</div>
          <div className="ast-kvCell ast-kValue">{row[5]}</div>
        </div>
      ))}
    </div>
  );
}

function TradesTable() {
  return (
    <div className="ast-scroll">
      <table className="ast-table">
        <thead>
          <tr>
            <th rowSpan={2}>Currency</th>
            <th colSpan={3}>Longs</th>
            <th colSpan={3}>Shorts</th>
            <th colSpan={6}>Total</th>
          </tr>
          <tr>
            <th>Trades</th>
            <th>Pips</th>
            <th>Profit($)</th>
            <th>Trades</th>
            <th>Pips</th>
            <th>Profit($)</th>
            <th>Trades</th>
            <th>Pips</th>
            <th>Profit($)</th>
            <th>Won(%)</th>
            <th>Lost(%)</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {tradeSummaryRows.map((row) => (
            <tr key={row.currency}>
              <td>{row.currency}</td>
              <td>{row.longTrades}</td>
              <td className={row.longPips >= 0 ? "is-up" : "is-down"}>{row.longPips.toFixed(1)}</td>
              <td className={row.longProfit >= 0 ? "is-up" : "is-down"}>{fmtMoney(row.longProfit)}</td>
              <td>{row.shortTrades}</td>
              <td className={row.shortPips >= 0 ? "is-up" : "is-down"}>{row.shortPips.toFixed(1)}</td>
              <td className={row.shortProfit >= 0 ? "is-up" : "is-down"}>{fmtMoney(row.shortProfit)}</td>
              <td>{row.totalTrades}</td>
              <td className={row.totalPips >= 0 ? "is-up" : "is-down"}>{row.totalPips.toFixed(1)}</td>
              <td className={row.totalProfit >= 0 ? "is-up" : "is-down"}>{fmtMoney(row.totalProfit)}</td>
              <td>{row.wonPct}</td>
              <td>{row.lostPct}</td>
              <td className="ast-iconCell">▮▯</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HourlyBars() {
  const maxStack = Math.max(...hourlyBuckets.map((b) => b.winners + b.losers), 1);

  return (
    <div className="ast-chartPanel">
      <div className="ast-chartTitle">Winners Vs. Losers</div>
      <div className="ast-hourly">
        <div className="ast-hourlyGrid" aria-hidden="true" />
        <div className="ast-hourlyBars">
          {hourlyBuckets.map((bucket) => {
            const total = bucket.winners + bucket.losers;
            return (
              <div key={bucket.hour} className="ast-hourCol">
                <div className="ast-hourStack">
                  <div
                    className="ast-hourSeg ast-hourWin"
                    style={{ height: `${(bucket.winners / maxStack) * 180}px` }}
                  />
                  <div
                    className="ast-hourSeg ast-hourLoss"
                    style={{ height: `${(bucket.losers / maxStack) * 180}px` }}
                  />
                  <span className="ast-hourTotal">{total}</span>
                </div>
                <span className="ast-hourLabel">{bucket.hour}</span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="ast-legend">
        <span><i className="ast-dot ast-win" /> Winners</span>
        <span><i className="ast-dot ast-loss" /> Losers</span>
      </div>
    </div>
  );
}

function DailyMatrix() {
  return (
    <div className="ast-cardWhite">
      <div className="ast-chartTitle">Daily Distribution (mock)</div>
      <div className="ast-scroll">
        <table className="ast-table ast-heatTable">
          <thead>
            <tr>
              <th>Day</th>
              <th>08-10</th>
              <th>10-12</th>
              <th>12-14</th>
              <th>14-16</th>
              <th>16-18</th>
            </tr>
          </thead>
          <tbody>
            {dailyHeat.map(([day, ...values]) => (
              <tr key={day}>
                <td>{day}</td>
                {values.map((v, idx) => (
                  <td key={`${day}-${idx}`}>
                    <span className={`ast-heatCell ast-level-${Math.min(v, 4)}`}>{v}</span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RiskOfRuinTable() {
  return (
    <div className="ast-scroll">
      <table className="ast-table ast-riskTable">
        <thead>
          <tr>
            <th>Loss Size</th>
            {riskColumns.map((col) => (
              <th key={col.lossSize}>{col.lossSize}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Probability of Loss</td>
            {riskColumns.map((col) => (
              <td key={`prob-${col.lossSize}`}>{col.probability}</td>
            ))}
          </tr>
          <tr>
            <td>Consecutive Losing Trades</td>
            {riskColumns.map((col) => (
              <td key={`streak-${col.lossSize}`}>{col.streak}</td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function DurationPanel() {
  const bars = [
    { label: "Avg Trade Length", value: 4, max: 20 },
    { label: "Avg Win Length", value: 6, max: 20 },
    { label: "Avg Loss Length", value: 3, max: 20 },
    { label: "Max Trade Length", value: 18, max: 20 }
  ];

  return (
    <div className="ast-cardWhite">
      <div className="ast-chartTitle">Duration</div>
      <div className="ast-durationList">
        {bars.map((bar) => (
          <div key={bar.label} className="ast-durationRow">
            <span>{bar.label}</span>
            <div className="ast-durationTrack">
              <div className="ast-durationFill" style={{ width: `${(bar.value / bar.max) * 100}%` }} />
            </div>
            <strong>{bar.value}m</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function MaeMfePanel() {
  const points = [
    { x: 14, y: 22 },
    { x: 28, y: 18 },
    { x: 37, y: 35 },
    { x: 52, y: 27 },
    { x: 68, y: 43 },
    { x: 78, y: 31 }
  ];
  return (
    <div className="ast-cardWhite">
      <div className="ast-chartTitle">MAE / MFE Scatter (mock)</div>
      <div className="ast-scatter">
        <div className="ast-hourlyGrid" aria-hidden="true" />
        {points.map((p, idx) => (
          <span key={idx} className="ast-point" style={{ left: `${p.x}%`, bottom: `${p.y}%` }} />
        ))}
        <div className="ast-axisLabel ast-axisX">MFE</div>
        <div className="ast-axisLabel ast-axisY">MAE</div>
      </div>
    </div>
  );
}

function SummaryPanel() {
  const cards = [
    { label: "Win Rate", value: "50%" },
    { label: "Profit Factor", value: "1.44" },
    { label: "Expectancy", value: "$205.00" },
    { label: "Avg Trade", value: "4m" }
  ];
  return (
    <div className="ast-summaryCards">
      {cards.map((card) => (
        <div key={card.label} className="ast-summaryCard">
          <div className="ast-summaryLabel">{card.label}</div>
          <div className="ast-summaryValue">{card.value}</div>
        </div>
      ))}
      <div className="ast-cardWhite ast-summaryWide">
        <div className="ast-chartTitle">Summary Notes</div>
        <ul className="ast-noteList">
          <li>MVP: map this tab to `/api/accounts/:id/stats` and aggregated `daily-metrics`.</li>
          <li>Show range switch (7d / 30d / 90d / all) and recompute metrics client-side or server-side.</li>
          <li>Keep values normalized per account currency.</li>
        </ul>
      </div>
    </div>
  );
}

function renderTabContent(activeTab: AdvancedTab) {
  switch (activeTab) {
    case "advanced":
      return <AdvancedGrid />;
    case "trades":
      return <TradesTable />;
    case "summary":
      return <SummaryPanel />;
    case "hourly":
      return <HourlyBars />;
    case "daily":
      return <DailyMatrix />;
    case "risk":
      return <RiskOfRuinTable />;
    case "duration":
      return <DurationPanel />;
    case "mae":
      return <MaeMfePanel />;
    default:
      return null;
  }
}

export default function AdvancedStatisticsPanel() {
  const [activeTab, setActiveTab] = useState<AdvancedTab>("advanced");

  return (
    <section className="ast-shell" aria-labelledby="advanced-statistics-heading">
      <div className="ast-tabs" role="tablist" aria-label="Advanced statistics tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`ast-tab ${activeTab === tab.id ? "is-active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="ast-content">
        <h2 id="advanced-statistics-heading" className="ast-srOnly">Advanced Statistics</h2>
        {renderTabContent(activeTab)}
      </div>
    </section>
  );
}
