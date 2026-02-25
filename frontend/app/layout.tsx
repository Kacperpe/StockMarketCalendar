import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";

export const metadata = {
  title: "Trading Monitoring MVP",
  description: "Monitoring kont tradingowych MT5 / cTrader"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pl">
      <body>
        <div className="container">
          <nav className="nav">
            <Link className="pill" href="/">Dashboard</Link>
            <Link className="pill" href="/login">Login</Link>
            <Link className="pill" href="/register">Register</Link>
            <Link className="pill" href="/accounts">Accounts</Link>
            <Link className="pill" href="/account/1/overview">Overview</Link>
            <Link className="pill" href="/account/1/pnl">PnL</Link>
            <Link className="pill" href="/account/1/trades">Trades</Link>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}

