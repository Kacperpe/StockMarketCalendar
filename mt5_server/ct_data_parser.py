"""
cTrader data → same dict format as MT5 data_parser.py.

Monetary values in cTrader protos are in "cents" (÷ 100 to get currency units).
Prices are raw floating point (no scaling needed).
Volume is in "centilots": 100 centilots = 1 standard lot.
"""

import logging
import math
import statistics as stat_mod
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_CENTS = 100          # divide CTrader monetary ints by this
_CENTILOTS = 100      # divide volume by this to get standard lots


# ── Account ───────────────────────────────────────────────────────────────────

def parse_ct_account(trader, positions: list, spot_prices: dict) -> dict:
    """
    Convert ProtoOATrader + open positions → same format as MT5 parse_account().
    `trader` is a protobuf ProtoOATrader object.
    """
    balance = (trader.balance or 0) / _CENTS

    # Approximate floating P&L from open positions
    floating = sum(
        _approx_position_pnl(p, spot_prices)
        for p in positions
    )
    equity = round(balance + floating, 2)

    margin = getattr(trader, "marginUsed", 0) or 0
    margin /= _CENTS

    return {
        "login":            trader.ctidTraderAccountId,
        "name":             f"Account {trader.ctidTraderAccountId}",
        "server":           getattr(trader, "brokerName", "cTrader"),
        "currency":         "",        # filled later via deposit asset lookup
        "balance":          round(balance, 2),
        "equity":           equity,
        "margin":           round(margin, 2),
        "free_margin":      round(equity - margin, 2),
        "margin_level_pct": round(equity / margin * 100, 2) if margin > 0 else None,
        "floating_pnl":     round(floating, 2),
        "leverage":         (getattr(trader, "leverageInCents", 0) or 0) // _CENTS or None,
    }


# ── Positions ─────────────────────────────────────────────────────────────────

def parse_ct_positions(positions: list, symbol_map: dict, spot_prices: dict) -> list:
    """
    Convert list of ProtoOAPosition → same format as MT5 parse_positions().
    """
    result = []
    for p in positions:
        td          = p.tradeData
        sym_id      = td.symbolId
        symbol_name = symbol_map.get(sym_id, f"SYM_{sym_id}")
        side        = "BUY" if td.tradeSide == 1 else "SELL"
        lots        = td.volume / _CENTILOTS

        entry_price   = getattr(p, "price", 0) or 0
        spots         = spot_prices.get(sym_id, {})
        current_price = spots.get("ask" if side == "BUY" else "bid", entry_price)

        swap         = (getattr(p, "swap", 0)       or 0) / _CENTS
        commission   = (getattr(p, "commission", 0) or 0) / _CENTS
        pnl_approx   = _approx_position_pnl(p, spot_prices)
        pnl_net      = round(pnl_approx + swap + commission, 2)

        open_ts = getattr(p, "openTimestamp", None) or getattr(td, "openTimestamp", None)
        open_time = (
            datetime.utcfromtimestamp(open_ts / 1000).isoformat()
            if open_ts else ""
        )

        result.append({
            "ticket":         p.positionId,
            "symbol":         symbol_name,
            "type":           side,
            "volume":         round(lots, 2),
            "open_price":     entry_price,
            "current_price":  round(current_price, 5),
            "sl":             getattr(p, "stopLoss",   None) or None,
            "tp":             getattr(p, "takeProfit", None) or None,
            "profit_raw":     round(pnl_approx, 2),
            "swap":           round(swap, 2),
            "pnl_net":        pnl_net,
            "open_time":      open_time,
            "position_id":    p.positionId,
            "magic":          0,
            "comment":        "",
        })
    return result


# ── Deal history helpers ───────────────────────────────────────────────────────

def _ct_deals_to_rows(deals) -> list:
    """
    Convert ProtoOADeal list → list of dicts parallel to MT5 deal DataFrames.
    Only deals with closePositionDetail (= exit deals) carry usable P&L.
    """
    rows = []
    for d in deals:
        cpd = getattr(d, "closePositionDetail", None)
        if cpd is None:
            continue  # entry deal or incomplete
        if d.dealStatus != 2:  # 2 = FILLED; skip partially-filled/rejected
            continue

        gross   = (cpd.grossProfit or 0) / _CENTS
        swap    = (cpd.swap        or 0) / _CENTS
        comm    = ((cpd.commission or 0) + (getattr(d, "commission", 0) or 0)) / _CENTS
        volume  = (cpd.closedVolume or 0) / _CENTILOTS
        ts      = (d.executionTimestamp or d.createTimestamp or 0) / 1000

        rows.append({
            "position_id":   d.positionId,
            "symbol_id":     d.symbolId,
            "symbol":        "",   # filled by caller using symbol_map
            "type":          "BUY"  if d.tradeSide == 1 else "SELL",
            "profit":        round(gross, 2),
            "swap":          round(swap,  2),
            "commission":    round(comm,  2),
            "volume":        round(volume, 2),
            "open_price":    cpd.entryPrice,
            "close_price":   d.executionPrice,
            "pnl_net":       round(gross + swap + comm, 2),
            "time":          datetime.utcfromtimestamp(ts) if ts else datetime.utcnow(),
            "duration_sec":  0,  # CT doesn't provide open time in deal directly
        })
    return rows


# ── Statistics (mirrors MT5 parse_statistics + compute_full_stats) ────────────

def parse_ct_statistics(deals, days: int = 30, symbol_map: dict = None) -> dict:
    """Like MT5 parse_statistics() but from CT deals."""
    symbol_map = symbol_map or {}
    rows = _ct_deals_to_rows(deals)
    if not rows:
        return {"error": "no closed trades", "days": days}

    trades = _aggregate_ct_rows(rows, symbol_map)
    wins   = [t for t in trades if t["pnl_net"] > 0]
    losses = [t for t in trades if t["pnl_net"] < 0]
    total  = len(trades)

    gp  = sum(t["pnl_net"] for t in wins)
    gl  = abs(sum(t["pnl_net"] for t in losses))

    return {
        "period_days":      days,
        "total_trades":     total,
        "winning_trades":   len(wins),
        "losing_trades":    len(losses),
        "win_rate_pct":     round(len(wins) / total * 100, 2) if total else 0,
        "net_profit":       round(sum(t["pnl_net"] for t in trades), 2),
        "gross_profit":     round(gp, 2),
        "gross_loss":       round(gl, 2),
        "profit_factor":    round(gp / gl, 2) if gl > 0 else None,
        "avg_win":          round(sum(t["pnl_net"] for t in wins)   / len(wins),   2) if wins   else 0,
        "avg_loss":         round(sum(t["pnl_net"] for t in losses) / len(losses), 2) if losses else 0,
        "best_trade":       round(max(t["pnl_net"] for t in trades), 2) if trades else 0,
        "worst_trade":      round(min(t["pnl_net"] for t in trades), 2) if trades else 0,
        "total_commission": round(sum(t["commission"] for t in trades), 2),
        "total_swap":       round(sum(t["swap"]       for t in trades), 2),
    }


def compute_ct_full_stats(deals, balance_start: float, balance_end: float,
                          currency: str, days: int, symbol_map: dict = None) -> dict:
    """Like MT5 compute_full_stats() but from CT deals."""
    symbol_map = symbol_map or {}
    rows    = _ct_deals_to_rows(deals)
    trades  = _aggregate_ct_rows(rows, symbol_map)

    if not trades:
        return {"error": "Brak zamkniętych transakcji w tym okresie", "currency": currency}

    total_trades = len(trades)
    wins   = [t for t in trades if t["pnl_net"] > 0]
    losses = [t for t in trades if t["pnl_net"] < 0]

    win_rate     = len(wins) / total_trades if total_trades else 0.0
    gain_pct     = ((balance_end - balance_start) / abs(balance_start) * 100) if balance_start else 0.0
    total_profit = sum(t["pnl_net"] for t in trades)
    total_lots   = sum(t["volume"]  for t in trades)

    avg_win_eur  = (sum(t["pnl_net"] for t in wins)   / len(wins))   if wins   else 0.0
    avg_loss_eur = (sum(t["pnl_net"] for t in losses) / len(losses)) if losses else 0.0

    longs      = [t for t in trades if t["type"] == "BUY"]
    shorts     = [t for t in trades if t["type"] == "SELL"]
    longs_won  = [t for t in longs  if t["pnl_net"] > 0]
    shorts_won = [t for t in shorts if t["pnl_net"] > 0]

    best_t  = max(trades, key=lambda t: t["pnl_net"])
    worst_t = min(trades, key=lambda t: t["pnl_net"])

    gp = sum(t["pnl_net"] for t in wins)
    gl = abs(sum(t["pnl_net"] for t in losses))
    profit_factor = round(gp / gl, 2) if gl > 0 else None

    pnl_list = [t["pnl_net"] for t in trades]
    std_dev  = round(stat_mod.stdev(pnl_list), 2) if len(pnl_list) > 1 else 0.0
    mean_pnl = sum(pnl_list) / len(pnl_list)
    sharpe   = round(mean_pnl / std_dev, 2) if std_dev > 0 else 0.0

    seq    = [1 if t["pnl_net"] > 0 else 0 for t in trades]
    N, W   = len(seq), sum(seq)
    L      = N - W
    z_score = z_prob = 0.0
    if W > 0 and L > 0 and N > 2:
        R         = sum(1 for i in range(1, N) if seq[i] != seq[i - 1]) + 1
        exp_R     = (2 * W * L / N) + 1
        var_num   = 2 * W * L * (2 * W * L - N)
        var_den   = N ** 2 * (N - 1)
        if var_den > 0 and var_num / var_den > 0:
            z_score = round((R - exp_R) / math.sqrt(var_num / var_den), 2)
            z_prob  = round(_norm_cdf(abs(z_score)) * 100, 2)

    expectancy_eur = round(win_rate * avg_win_eur + (1 - win_rate) * avg_loss_eur, 2)

    durations = [t["duration_sec"] for t in trades if t["duration_sec"] > 0]
    avg_dur   = round(sum(durations) / len(durations)) if durations else 0

    ahpr_returns = []
    rb = balance_start if balance_start > 0 else balance_end
    for t in trades:
        if rb > 0:
            ahpr_returns.append(t["pnl_net"] / rb)
        rb += t["pnl_net"]
    if ahpr_returns:
        ahpr = round(sum(ahpr_returns) / len(ahpr_returns) * 100, 4)
        prod = math.prod(1 + r for r in ahpr_returns)
        ghpr = round((prod ** (1 / len(ahpr_returns)) - 1) * 100, 4)
    else:
        ahpr = ghpr = 0.0

    return {
        "currency":        currency,
        "period_days":     days,
        "gain_pct":        round(gain_pct, 2),
        "profit":          round(total_profit, 2),
        "pips":            0.0,       # not available without contract info
        "win_rate_pct":    round(win_rate * 100, 1),
        "total_trades":    total_trades,
        "total_lots":      round(total_lots, 2),
        "winning_trades":  len(wins),
        "losing_trades":   len(losses),
        "avg_win_eur":     round(avg_win_eur, 2),
        "avg_loss_eur":    round(avg_loss_eur, 2),
        "avg_win_pips":    0.0,
        "avg_loss_pips":   0.0,
        "longs_total":     len(longs),
        "longs_won":       len(longs_won),
        "longs_win_pct":   round(len(longs_won) / len(longs) * 100, 1) if longs else 0.0,
        "shorts_total":    len(shorts),
        "shorts_won":      len(shorts_won),
        "shorts_win_pct":  round(len(shorts_won) / len(shorts) * 100, 1) if shorts else 0.0,
        "best_trade_eur":   best_t["pnl_net"],
        "best_trade_date":  best_t["close_time"],
        "best_trade_pips":  0.0,
        "worst_trade_eur":  worst_t["pnl_net"],
        "worst_trade_date": worst_t["close_time"],
        "worst_trade_pips": 0.0,
        "profit_factor":   profit_factor,
        "std_dev":         std_dev,
        "sharpe_ratio":    sharpe,
        "z_score":         z_score,
        "z_probability":   z_prob,
        "expectancy_eur":  expectancy_eur,
        "expectancy_pips": 0.0,
        "avg_trade_sec":   avg_dur,
        "avg_trade_fmt":   _fmt_duration(avg_dur),
        "ahpr_pct":        ahpr,
        "ghpr_pct":        ghpr,
        "gross_profit":    round(gp, 2),
        "gross_loss":      round(gl, 2),
    }


def _cashflow_stats(cash_flows: list | None) -> tuple[float, float, float, float | None]:
    deposits = 0.0
    withdrawals = 0.0
    net = 0.0
    last_balance = None

    for item in cash_flows or []:
        digits = int(getattr(item, "moneyDigits", 2) or 2)
        scale = 10 ** digits

        delta = (getattr(item, "delta", 0) or 0) / scale
        balance = (getattr(item, "balance", 0) or 0) / scale

        if delta > 0:
            deposits += delta
        elif delta < 0:
            withdrawals += abs(delta)
        net += delta
        last_balance = balance

    return round(deposits, 2), round(withdrawals, 2), round(net, 2), last_balance


def compute_ct_overview(
    deals_all,
    balance_now: float | None,
    currency: str,
    cash_flows: list | None = None,
    equity_now: float | None = None,
) -> dict:
    """Overview stats (gain%, avg daily/monthly, max DD) from CT history."""
    rows = _ct_deals_to_rows(deals_all)
    trades = _aggregate_ct_rows(rows, {})

    total_profit = round(sum(t["pnl_net"] for t in trades), 2)
    deposits, withdrawals, net_deposits, last_cash_balance = _cashflow_stats(cash_flows)

    balance = float(balance_now or 0.0)
    if balance == 0.0:
        if net_deposits != 0.0 or total_profit != 0.0:
            balance = round(net_deposits + total_profit, 2)
        elif last_cash_balance is not None:
            balance = float(last_cash_balance)

    equity = float(equity_now if equity_now is not None else balance)
    if equity == 0.0 and balance != 0.0:
        equity = balance

    if trades:
        times = [datetime.fromisoformat(t["close_time"]) for t in trades if t["close_time"]]
        if times:
            first = min(times)
            t_days = max(1.0, (datetime.utcnow() - first).total_seconds() / 86400)
            daily = round(total_profit / t_days, 2)
            monthly = round(daily * 30.44, 2)
        else:
            daily = monthly = 0.0
    else:
        daily = monthly = 0.0

    # Gain is based on net deposits when available; fallback to inferred starting balance.
    base_capital = float(net_deposits)
    if base_capital <= 0:
        inferred_start = round(balance - total_profit, 2)
        if inferred_start > 0:
            base_capital = inferred_start
            if deposits == 0 and withdrawals == 0:
                deposits = inferred_start
    gain_pct = round((total_profit / base_capital * 100) if base_capital > 0 else 0.0, 2)

    # Approx max drawdown from running balance
    running = balance
    peak = running
    max_dd = 0.0
    for trade in sorted(trades, key=lambda x: x["close_time"], reverse=True):
        running -= trade["pnl_net"]
        if running > peak:
            peak = running
        if peak > 0:
            dd = (peak - running) / peak * 100
            if dd > max_dd:
                max_dd = dd

    return {
        "balance":          round(balance, 2),
        "equity":           round(equity, 2),
        "currency":         currency,
        "total_profit":     total_profit,
        "deposits":         round(deposits, 2),
        "withdrawals":      round(withdrawals, 2),
        "gain_pct":         gain_pct,
        "daily_avg":        daily,
        "monthly_avg":      monthly,
        "max_drawdown_pct": round(max_dd, 2),
    }


def compute_ct_equity_curve(deals_all) -> list:
    """Reconstruct balance curve from CT deal history."""
    rows = _ct_deals_to_rows(deals_all)
    rows_sorted = sorted(rows, key=lambda r: r["time"])
    balance = 0.0
    points  = []
    for r in rows_sorted:
        balance += r["pnl_net"]
        points.append({
            "ts":      r["time"].isoformat(),
            "balance": round(balance, 2),
        })
    return points


def compute_ct_calendar(deals, year: int, month: int, symbol_map: dict = None) -> dict:
    """Compute calendar P&L from CT deals. Same output format as data_calendar."""
    from calendar import monthrange

    symbol_map = symbol_map or {}
    rows   = _ct_deals_to_rows(deals)
    trades = _aggregate_ct_rows(rows, symbol_map)

    day_data: dict = {}
    for t in trades:
        if not t["close_time"]:
            continue
        dt   = datetime.fromisoformat(t["close_time"])
        date = str(dt.date())

        entry = day_data.setdefault(date, {"pnl": 0.0, "trades": 0, "wins": 0, "losses": 0})
        entry["pnl"]    = round(entry["pnl"] + t["pnl_net"], 2)
        entry["trades"] += 1
        if t["pnl_net"] > 0:
            entry["wins"]   += 1
        elif t["pnl_net"] < 0:
            entry["losses"] += 1

    for date, entry in day_data.items():
        total = entry["trades"]
        entry["win_rate"] = round(entry["wins"] / total * 100, 2) if total > 0 else 0.0

    week_data = _calc_weeks(year, month, day_data)
    return {"days": day_data, "weeks": week_data}


# ── Private helpers ────────────────────────────────────────────────────────────

def _approx_position_pnl(position, spot_prices: dict) -> float:
    """
    Rough unrealized P&L estimate.
    Works well for forex direct-quote pairs (EUR/USD, GBP/USD, etc.).
    For other instrument types accuracy varies.
    """
    td     = position.tradeData
    side   = td.tradeSide            # 1=BUY, 2=SELL
    sym_id = td.symbolId
    lots   = td.volume / _CENTILOTS

    entry = getattr(position, "price", None) or 0
    spots = spot_prices.get(sym_id, {})
    current = spots.get("ask" if side == 1 else "bid", entry)

    if not entry or not current:
        return 0.0

    direction = 1 if side == 1 else -1
    # Generic formula; contract size 100 000 assumed (forex standard lot)
    return round(direction * (current - entry) * lots * 100_000, 2)


def _aggregate_ct_rows(rows: list, symbol_map: dict) -> list:
    """Group exit rows by positionId → one trade per position."""
    groups = defaultdict(list)
    for r in rows:
        groups[r["position_id"]].append(r)

    trades = []
    for pos_id, pos_rows in groups.items():
        pos_rows.sort(key=lambda r: r["time"])
        total_pnl   = sum(r["pnl_net"]    for r in pos_rows)
        total_swap  = sum(r["swap"]       for r in pos_rows)
        total_comm  = sum(r["commission"] for r in pos_rows)
        total_vol   = sum(r["volume"]     for r in pos_rows)
        close_time  = max(r["time"] for r in pos_rows)
        sym_id      = pos_rows[0]["symbol_id"]
        sym_name    = symbol_map.get(sym_id, pos_rows[0].get("symbol") or f"SYM_{sym_id}")

        trades.append({
            "position_id":   pos_id,
            "symbol":        sym_name,
            "type":          pos_rows[0]["type"],
            "volume":        round(total_vol, 2),
            "open_price":    pos_rows[0]["open_price"],
            "close_price":   pos_rows[-1]["close_price"],
            "open_time":     "",
            "close_time":    close_time.isoformat(),
            "duration_sec":  0,
            "profit":        round(sum(r["profit"] for r in pos_rows), 2),
            "swap":          round(total_swap, 2),
            "commission":    round(total_comm, 2),
            "pnl_net":       round(total_pnl, 2),
            "pips":          0.0,
        })

    trades.sort(key=lambda t: t["close_time"])
    return trades


def _calc_weeks(year: int, month: int, day_data: dict) -> dict:
    from calendar import monthrange
    from datetime import date as date_cls

    _, days_in_month = monthrange(year, month)
    weeks: dict = defaultdict(lambda: {"pnl": 0.0, "trading_days": 0})
    week_num = 1

    for day in range(1, days_in_month + 1):
        d    = date_cls(year, month, day)
        dstr = str(d)
        if dstr in day_data:
            weeks[week_num]["pnl"] = round(weeks[week_num]["pnl"] + day_data[dstr]["pnl"], 2)
            weeks[week_num]["trading_days"] += 1
        if d.weekday() == 6:
            week_num += 1

    return {str(k): v for k, v in weeks.items()}


def _norm_cdf(x: float) -> float:
    import math
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def _fmt_duration(seconds: int) -> str:
    if seconds <= 0: return "0s"
    if seconds < 60: return f"{seconds}s"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s" if s else f"{m}m"
    if seconds < 86400:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}h {m}m" if m else f"{h}h"
    d, rem = divmod(seconds, 86400)
    h = rem // 3600
    return f"{d}d {h}h" if h else f"{d}d"
