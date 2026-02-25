"use client";

import { useMemo, useState } from "react";

type CalendarTrade = {
  symbol: string;
  side: "buy" | "sell";
  pnl: number;
  fees: number;
};

type CalendarDay = {
  day: number;
  netPnl: number;
  trades: number;
  winRate: number;
  week: number;
  isCurrentMonth?: boolean;
  details: CalendarTrade[];
};

const dayHeaders = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const monthDays: CalendarDay[] = [
  { day: 1, netPnl: 0, trades: 0, winRate: 0, week: 1, details: [] },
  { day: 2, netPnl: 0, trades: 0, winRate: 0, week: 1, details: [] },
  { day: 3, netPnl: 0, trades: 0, winRate: 0, week: 1, details: [] },
  { day: 4, netPnl: 0, trades: 0, winRate: 0, week: 1, details: [] },
  { day: 5, netPnl: 0, trades: 0, winRate: 0, week: 1, details: [] },
  { day: 6, netPnl: 0, trades: 0, winRate: 0, week: 1, details: [] },
  { day: 7, netPnl: 0, trades: 0, winRate: 0, week: 1, details: [] },
  { day: 8, netPnl: 0, trades: 0, winRate: 0, week: 2, details: [] },
  { day: 9, netPnl: 0, trades: 0, winRate: 0, week: 2, details: [] },
  { day: 10, netPnl: 0, trades: 0, winRate: 0, week: 2, details: [] },
  { day: 11, netPnl: 0, trades: 0, winRate: 0, week: 2, details: [] },
  { day: 12, netPnl: 0, trades: 0, winRate: 0, week: 2, details: [] },
  { day: 13, netPnl: 0, trades: 0, winRate: 0, week: 2, details: [] },
  { day: 14, netPnl: -91.5, trades: 2, winRate: 0, week: 2, details: [
    { symbol: "NAS100", side: "sell", pnl: -53.1, fees: 2.1 },
    { symbol: "EURUSD", side: "buy", pnl: -38.4, fees: 1.9 }
  ] },
  { day: 15, netPnl: 0, trades: 0, winRate: 0, week: 3, details: [] },
  { day: 16, netPnl: 0, trades: 0, winRate: 0, week: 3, details: [] },
  { day: 17, netPnl: 0, trades: 0, winRate: 0, week: 3, details: [] },
  { day: 18, netPnl: 0, trades: 0, winRate: 0, week: 3, details: [] },
  { day: 19, netPnl: 0, trades: 0, winRate: 0, week: 3, details: [] },
  { day: 20, netPnl: 0, trades: 0, winRate: 0, week: 3, details: [] },
  { day: 21, netPnl: 0, trades: 0, winRate: 0, week: 3, details: [] },
  { day: 22, netPnl: 0, trades: 0, winRate: 0, week: 4, details: [] },
  { day: 23, netPnl: 0, trades: 0, winRate: 0, week: 4, details: [] },
  { day: 24, netPnl: 0, trades: 0, winRate: 0, week: 4, details: [] },
  { day: 25, netPnl: 436.41, trades: 50, winRate: 36, week: 4, details: [
    { symbol: "XAUUSD", side: "buy", pnl: 210.3, fees: 8.5 },
    { symbol: "XAUUSD", side: "sell", pnl: 120.1, fees: 6.7 },
    { symbol: "EURUSD", side: "buy", pnl: 106.01, fees: 3.2 }
  ] },
  { day: 26, netPnl: 0, trades: 0, winRate: 0, week: 4, details: [] },
  { day: 27, netPnl: 0, trades: 0, winRate: 0, week: 4, details: [] },
  { day: 28, netPnl: 0, trades: 0, winRate: 0, week: 4, details: [] }
];

function euro(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function pnlClass(value: number): string {
  if (value > 0) return "is-up";
  if (value < 0) return "is-down";
  return "is-flat";
}

export default function WhitePnlCalendar() {
  const [selectedDay, setSelectedDay] = useState<number>(25);

  const selected = monthDays.find((day) => day.day === selectedDay) ?? monthDays[0];

  const weekCards = useMemo(() => {
    const byWeek = new Map<number, { sum: number; days: number }>();
    for (const day of monthDays) {
      const current = byWeek.get(day.week) ?? { sum: 0, days: 0 };
      if (day.trades > 0) {
        current.sum += day.netPnl;
        current.days += 1;
      }
      byWeek.set(day.week, current);
    }
    return [1, 2, 3, 4, 5].map((week) => ({
      week,
      sum: byWeek.get(week)?.sum ?? 0,
      days: byWeek.get(week)?.days ?? 0
    }));
  }, []);

  return (
    <section className="wc-shell">
      <header className="wc-header">
        <div className="wc-account">
          <div className="wc-logo" aria-hidden="true">F</div>
          <div>
            <div className="wc-name">Fintokei</div>
            <div className="wc-meta">SwiftTrader: 40k / 200k</div>
          </div>
        </div>
        <div className="wc-topStats">
          <span>Masters: <strong>1</strong></span>
          <span>Slaves: <strong>1</strong></span>
          <span>Live: <strong>EUR 0</strong></span>
          <span>Payouts: <strong>EUR 0</strong></span>
        </div>
      </header>

      <div className="wc-layout">
        <div className="wc-main">
          <div className="wc-weekdays">
            {dayHeaders.map((day) => (
              <span key={day}>{day}</span>
            ))}
          </div>

          <div className="wc-grid">
            {monthDays.map((day) => {
              const selectedCls = selectedDay === day.day ? "is-selected" : "";
              const stateCls = day.netPnl > 0 ? "is-profit" : day.netPnl < 0 ? "is-loss" : "is-empty";
              return (
                <button
                  key={day.day}
                  type="button"
                  className={`wc-cell ${stateCls} ${selectedCls}`}
                  onClick={() => setSelectedDay(day.day)}
                >
                  <span className="wc-dayNumber">{day.day}</span>
                  {day.trades > 0 ? (
                    <span className="wc-cellMeta">
                      <strong className={pnlClass(day.netPnl)}>{euro(day.netPnl)}</strong>
                      <small>{day.trades} trades</small>
                      <small>WR: {day.winRate.toFixed(0)}%</small>
                    </span>
                  ) : null}
                </button>
              );
            })}
          </div>
        </div>

        <aside className="wc-sidebar">
          {weekCards.map((week) => (
            <div
              key={week.week}
              className={`wc-weekCard ${week.sum > 0 ? "is-profit" : week.sum < 0 ? "is-loss" : ""}`}
            >
              <div className="wc-weekLabel">Week {week.week}</div>
              <div className={`wc-weekValue ${pnlClass(week.sum)}`}>{euro(week.sum)}</div>
              <div className="wc-weekDays">{week.days} {week.days === 1 ? "day" : "days"}</div>
            </div>
          ))}
        </aside>
      </div>

      <div className="wc-details">
        <div className="wc-detailsHeader">
          <div>
            <h2 className="wc-title">Day Details - Feb {selected.day}, 2026</h2>
            <p className="wc-subtitle">
              Daily PnL, trades and fees (target integration: `/api/accounts/{'{id}'}/daily-metrics` + `/trades`).
            </p>
          </div>
          <div className={`wc-dayPnl ${pnlClass(selected.netPnl)}`}>{euro(selected.netPnl)}</div>
        </div>

        <div className="wc-summaryRow">
          <div className="wc-summaryItem">
            <span>Trades</span>
            <strong>{selected.trades}</strong>
          </div>
          <div className="wc-summaryItem">
            <span>Win Rate</span>
            <strong>{selected.winRate.toFixed(0)}%</strong>
          </div>
          <div className="wc-summaryItem">
            <span>Fees</span>
            <strong>{euro(selected.details.reduce((sum, trade) => sum + trade.fees, 0))}</strong>
          </div>
          <div className="wc-summaryItem">
            <span>Symbols</span>
            <strong>{new Set(selected.details.map((trade) => trade.symbol)).size}</strong>
          </div>
        </div>

        <div className="wc-tableWrap">
          <table className="wc-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>PnL</th>
                <th>Fees</th>
                <th>Net</th>
              </tr>
            </thead>
            <tbody>
              {selected.details.length > 0 ? (
                selected.details.map((trade, index) => {
                  const net = trade.pnl - trade.fees;
                  return (
                    <tr key={`${trade.symbol}-${index}`}>
                      <td>{trade.symbol}</td>
                      <td>{trade.side}</td>
                      <td className={pnlClass(trade.pnl)}>{euro(trade.pnl)}</td>
                      <td>{euro(-trade.fees)}</td>
                      <td className={pnlClass(net)}>{euro(net)}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="wc-emptyRow">No trades for this day.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

