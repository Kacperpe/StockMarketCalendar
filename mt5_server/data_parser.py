import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def parse_account(info) -> dict | None:
    if info is None:
        return None
    return {
        "login": info.login,
        "name": info.name,
        "server": info.server,
        "currency": info.currency,
        "balance": info.balance,
        "equity": info.equity,
        "margin": info.margin,
        "free_margin": info.margin_free,
        # margin_level może być 0 gdy brak pozycji
        "margin_level_pct": round(info.margin_level, 2) if info.margin_level else None,
        "floating_pnl": round(info.profit, 2),
        "leverage": info.leverage,
    }


def parse_positions(positions) -> list:
    if positions is None:
        return []
    result = []
    for p in positions:
        # TradePosition nie ma commission — jest tylko w historii dealów
        # pnl_net = profit + swap (bez commission)
        pnl_net = round(p.profit + p.swap, 2)
        result.append({
            "ticket": p.ticket,
            "symbol": p.symbol,
            "type": "BUY" if p.type == 0 else "SELL",
            "volume": p.volume,
            "open_price": p.price_open,
            "current_price": p.price_current,
            "sl": p.sl or None,
            "tp": p.tp or None,
            "profit_raw": round(p.profit, 2),   # samo floating P&L
            "swap": round(p.swap, 2),
            "pnl_net": pnl_net,                 # profit+swap
            "open_time": datetime.utcfromtimestamp(p.time).isoformat(),
            "position_id": p.identifier,
            "magic": p.magic,
            "comment": p.comment,
        })
    return result


def parse_statistics(days: int = 30) -> dict:
    """
    Agreguje po position_id (nie po deal.ticket) żeby uniknąć
    problemu z częściowymi zamknięciami i prowizjami jako osobnymi dealami.
    """
    date_from = datetime.utcnow() - timedelta(days=days)
    deals = mt5.history_deals_get(date_from, datetime.utcnow())

    if not deals:
        return {"error": "no data", "days": days}

    df = pd.DataFrame([{
        "ticket":      d.ticket,
        "position_id": d.position_id,
        "symbol":      d.symbol,
        "type":        d.type,
        "entry":       d.entry,   # 0=IN, 1=OUT, 2=INOUT
        "volume":      d.volume,
        "price":       d.price,
        "profit":      d.profit,
        "swap":        d.swap,
        "commission":  d.commission,
        "time":        datetime.utcfromtimestamp(d.time).isoformat(),
    } for d in deals])

    # Filtruj tylko zamknięcia (entry==1 lub INOUT==2)
    exits = df[df["entry"].isin([1, 2])].copy()

    if exits.empty:
        return {"error": "no closed trades", "days": days}

    # Agreguj po position_id — każda pozycja to jeden "trade"
    # (obsługuje częściowe zamknięcia: sumuje profit/swap/commission)
    trades = exits.groupby("position_id").agg(
        symbol=("symbol", "first"),
        profit=("profit", "sum"),
        swap=("swap", "sum"),
        commission=("commission", "sum"),
        volume=("volume", "sum"),
        close_time=("time", "last"),
    ).reset_index()

    trades["pnl_net"] = trades["profit"] + trades["swap"] + trades["commission"]

    wins   = trades[trades["pnl_net"] > 0]
    losses = trades[trades["pnl_net"] < 0]
    total  = len(trades)

    gross_profit = wins["pnl_net"].sum()
    gross_loss   = abs(losses["pnl_net"].sum())

    return {
        "period_days":      days,
        "total_trades":     total,
        "winning_trades":   len(wins),
        "losing_trades":    len(losses),
        "win_rate_pct":     round(len(wins) / total * 100, 2) if total > 0 else 0,
        "net_profit":       round(trades["pnl_net"].sum(), 2),
        "gross_profit":     round(gross_profit, 2),
        "gross_loss":       round(gross_loss, 2),
        # profit factor = gross_profit / gross_loss (Myfxbook-style)
        "profit_factor":    round(gross_profit / gross_loss, 2) if gross_loss > 0 else None,
        "avg_win":          round(wins["pnl_net"].mean(), 2) if len(wins) > 0 else 0,
        "avg_loss":         round(losses["pnl_net"].mean(), 2) if len(losses) > 0 else 0,
        "best_trade":       round(trades["pnl_net"].max(), 2) if total > 0 else 0,
        "worst_trade":      round(trades["pnl_net"].min(), 2) if total > 0 else 0,
        "total_commission": round(trades["commission"].sum(), 2),
        "total_swap":       round(trades["swap"].sum(), 2),
    }


def build_full_equity_curve() -> list:
    """
    Rekonstruuje krzywą bilansu od pierwszej transakcji na koncie.
    Zwraca listę punktów {ts, balance} posortowanych chronologicznie.
    """
    from datetime import datetime

    date_from = datetime(2000, 1, 1)
    date_to   = datetime.utcnow()
    deals     = mt5.history_deals_get(date_from, date_to)

    if not deals:
        return []

    balance = 0.0
    points  = []

    for d in sorted(deals, key=lambda x: x.time):
        # DEAL_TYPE_BALANCE = 2  (wpłaty, wypłaty, kredyty)
        if d.type == 2:
            balance += d.profit
        # DEAL_ENTRY_OUT = 1, DEAL_ENTRY_INOUT = 2  (zamknięcie pozycji)
        elif d.entry in (1, 2):
            balance += d.profit + d.commission + d.swap
        else:
            continue

        points.append({
            "ts":      datetime.utcfromtimestamp(d.time).isoformat(),
            "balance": round(balance, 2),
        })

    # Dodaj aktualny equity jako ostatni punkt (live)
    info = mt5.account_info()
    if info and points:
        points.append({
            "ts":      datetime.utcnow().isoformat(),
            "balance": round(info.equity, 2),
            "live":    True,
        })

    return points


def get_overview_stats() -> dict:
    """
    Liczy wszystkie statystyki potrzebne na dashboard:
    gain%, śr. dzienny, śr. miesięczny, max drawdown, balance, equity, total profit.
    """
    from datetime import datetime

    date_from = datetime(2000, 1, 1)
    date_to   = datetime.utcnow()

    info  = mt5.account_info()
    deals = mt5.history_deals_get(date_from, date_to)

    if not info:
        return {"error": "no MT5 data"}

    deposits     = 0.0
    withdrawals  = 0.0
    balance      = 0.0
    peak         = 0.0
    max_dd_pct   = 0.0
    trade_times  = []

    if deals:
        for d in sorted(deals, key=lambda x: x.time):
            if d.type == 2:              # DEAL_TYPE_BALANCE
                if d.profit >= 0:
                    deposits += d.profit
                else:
                    withdrawals += abs(d.profit)
                balance += d.profit
            elif d.entry in (1, 2):      # zamknięta pozycja
                balance += d.profit + d.commission + d.swap
                trade_times.append(d.time)
            else:
                continue

            # Drawdown względem szczytu bilansu
            if balance > peak:
                peak = balance
            if peak > 0:
                dd = (peak - balance) / peak * 100
                if dd > max_dd_pct:
                    max_dd_pct = dd

    net_deposits  = deposits - withdrawals
    total_profit  = round(info.balance - net_deposits, 2)
    gain_pct      = round((total_profit / net_deposits * 100) if net_deposits > 0 else 0.0, 2)

    if trade_times:
        first_trade_ts = min(trade_times)
        trading_days   = max(1.0, (datetime.utcnow().timestamp() - first_trade_ts) / 86400)
        daily_avg      = round(total_profit / trading_days, 2)
        monthly_avg    = round(daily_avg * 30.44, 2)
    else:
        daily_avg   = 0.0
        monthly_avg = 0.0

    return {
        "balance":          round(info.balance, 2),
        "equity":           round(info.equity, 2),
        "currency":         info.currency,
        "total_profit":     total_profit,
        "deposits":         round(deposits, 2),
        "withdrawals":      round(withdrawals, 2),
        "gain_pct":         gain_pct,
        "daily_avg":        daily_avg,
        "monthly_avg":      monthly_avg,
        "max_drawdown_pct": round(max_dd_pct, 2),
    }


# ── Myfxbook-style full statistics ────────────────────────────────────────────

def _norm_cdf(x: float) -> float:
    """Aproksymacja normalnego CDF bez scipy."""
    import math
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def _fmt_duration(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m = seconds // 60
        s = seconds % 60
        return f"{m}m {s}s" if s else f"{m}m"
    if seconds < 86400:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m" if m else f"{h}h"
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    return f"{d}d {h}h" if h else f"{d}d"


def _aggregate_trades(deals) -> list:
    """
    Grupuje deale po position_id i buduje listę kompletnych transakcji.
    Obsługuje częściowe zamknięcia, prowizje jako osobne deale (typ 3),
    oraz INOUT (entry=2).
    """
    from collections import defaultdict
    from datetime import datetime

    groups: dict = defaultdict(list)
    for d in deals:
        # Pomiń deale balansowe (depozyty/wypłaty) i te bez position_id
        if d.type == 2 or d.position_id == 0:
            continue
        groups[d.position_id].append(d)

    trades = []
    for pos_id, pos_deals in groups.items():
        pos_deals.sort(key=lambda x: x.time)

        entry_deals = [d for d in pos_deals if d.entry == 0]
        exit_deals  = [d for d in pos_deals if d.entry in (1, 2)]

        if not entry_deals or not exit_deals:
            continue

        entry_deal = entry_deals[0]
        symbol     = entry_deal.symbol

        # Pip size dla pary
        sym_info = mt5.symbol_info(symbol)
        pip_size = (sym_info.point * 10.0) if (sym_info and sym_info.point > 0) else 0.0001

        # Suma wyników
        total_profit     = sum(d.profit     for d in exit_deals)
        total_swap       = sum(d.swap       for d in pos_deals)
        total_commission = sum(d.commission for d in pos_deals)
        total_volume     = sum(d.volume     for d in exit_deals)
        pnl_net          = total_profit + total_swap + total_commission

        open_price  = entry_deal.price
        close_price = exit_deals[-1].price

        # Kierunek: DEAL_TYPE_BUY=0, DEAL_TYPE_SELL=1
        trade_type = "BUY" if entry_deal.type == 0 else "SELL"
        direction  = 1 if trade_type == "BUY" else -1

        pips = round((close_price - open_price) * direction / pip_size, 1) if pip_size > 0 else 0.0

        open_dt  = datetime.utcfromtimestamp(entry_deal.time)
        close_dt = datetime.utcfromtimestamp(exit_deals[-1].time)
        duration = int(exit_deals[-1].time - entry_deal.time)

        trades.append({
            "position_id":  pos_id,
            "symbol":       symbol,
            "type":         trade_type,
            "volume":       round(total_volume, 2),
            "open_price":   open_price,
            "close_price":  close_price,
            "open_time":    open_dt.isoformat(),
            "close_time":   close_dt.isoformat(),
            "duration_sec": duration,
            "profit":       round(total_profit, 2),
            "swap":         round(total_swap, 2),
            "commission":   round(total_commission, 2),
            "pnl_net":      round(pnl_net, 2),
            "pips":         pips,
        })

    trades.sort(key=lambda t: t["close_time"])
    return trades


def compute_full_stats(days: int = 30) -> dict:
    """
    Kompletne statystyki w stylu Myfxbook:
    Gain, Profit, Pips, Win%, Trades, Lots, Avg Win/Loss,
    Longs/Shorts Won, Best/Worst Trade, Profit Factor,
    Std Dev, Sharpe, Z-Score, Expectancy, Avg Length, AHPR/GHPR.
    """
    import statistics as stat_mod
    import math
    from datetime import datetime, timedelta
    from collections import defaultdict

    if days > 0:
        date_from = datetime.utcnow() - timedelta(days=days)
    else:
        date_from = datetime(2000, 1, 1)
    date_to = datetime.utcnow()

    deals   = mt5.history_deals_get(date_from, date_to)
    account = mt5.account_info()

    if not account:
        return {"error": "Brak danych konta MT5"}
    if not deals:
        return {"error": f"Brak historii transakcji za wskazany okres ({days} dni)", "currency": account.currency}

    # ── Balance na początku okresu (ze wszystkiej historii) ──────────────────
    all_deals    = mt5.history_deals_get(datetime(2000, 1, 1), date_to) or []
    period_start = int(date_from.timestamp())

    balance_start = 0.0
    for d in sorted(all_deals, key=lambda x: x.time):
        if d.time >= period_start:
            break
        if d.type == 2:
            balance_start += d.profit
        elif d.entry in (1, 2):
            balance_start += d.profit + d.commission + d.swap

    balance_end = account.balance

    # ── Zagregowane transakcje ───────────────────────────────────────────────
    trades = _aggregate_trades(list(deals))

    if not trades:
        return {"error": "Brak zamkniętych transakcji w tym okresie", "currency": account.currency}

    # ── Podstawowe ───────────────────────────────────────────────────────────
    total_trades = len(trades)
    wins   = [t for t in trades if t["pnl_net"] > 0]
    losses = [t for t in trades if t["pnl_net"] < 0]

    win_rate    = len(wins) / total_trades if total_trades else 0.0
    gain_pct    = ((balance_end - balance_start) / abs(balance_start) * 100) if balance_start != 0 else 0.0
    total_profit = sum(t["pnl_net"] for t in trades)
    total_pips   = sum(t["pips"]    for t in trades)
    total_lots   = sum(t["volume"]  for t in trades)

    # ── Avg Win / Loss ────────────────────────────────────────────────────────
    avg_win_eur  = (sum(t["pnl_net"] for t in wins)   / len(wins))   if wins   else 0.0
    avg_loss_eur = (sum(t["pnl_net"] for t in losses) / len(losses)) if losses else 0.0
    avg_win_pips  = (sum(t["pips"] for t in wins)   / len(wins))   if wins   else 0.0
    avg_loss_pips = (sum(t["pips"] for t in losses) / len(losses)) if losses else 0.0

    # ── Longs / Shorts ────────────────────────────────────────────────────────
    longs  = [t for t in trades if t["type"] == "BUY"]
    shorts = [t for t in trades if t["type"] == "SELL"]
    longs_won  = [t for t in longs  if t["pnl_net"] > 0]
    shorts_won = [t for t in shorts if t["pnl_net"] > 0]

    # ── Best / Worst ──────────────────────────────────────────────────────────
    best_t  = max(trades, key=lambda t: t["pnl_net"])
    worst_t = min(trades, key=lambda t: t["pnl_net"])
    best_pips_t  = max(trades, key=lambda t: t["pips"])
    worst_pips_t = min(trades, key=lambda t: t["pips"])

    # ── Profit Factor ─────────────────────────────────────────────────────────
    gross_profit = sum(t["pnl_net"] for t in wins)
    gross_loss   = abs(sum(t["pnl_net"] for t in losses))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else None

    # ── Std Dev ───────────────────────────────────────────────────────────────
    pnl_list = [t["pnl_net"] for t in trades]
    std_dev  = round(stat_mod.stdev(pnl_list), 2) if len(pnl_list) > 1 else 0.0
    mean_pnl = sum(pnl_list) / len(pnl_list)

    # ── Sharpe ────────────────────────────────────────────────────────────────
    sharpe = round(mean_pnl / std_dev, 2) if std_dev > 0 else 0.0

    # ── Z-Score ───────────────────────────────────────────────────────────────
    seq = [1 if t["pnl_net"] > 0 else 0 for t in trades]
    N   = len(seq)
    W   = sum(seq)
    L   = N - W
    z_score  = 0.0
    z_prob   = 0.0
    if W > 0 and L > 0 and N > 2:
        R          = sum(1 for i in range(1, N) if seq[i] != seq[i - 1]) + 1
        exp_R      = (2 * W * L / N) + 1
        var_R_num  = 2 * W * L * (2 * W * L - N)
        var_R_den  = N ** 2 * (N - 1)
        if var_R_den > 0 and var_R_num / var_R_den > 0:
            z_score = round((R - exp_R) / math.sqrt(var_R_num / var_R_den), 2)
            z_prob  = round(_norm_cdf(abs(z_score)) * 100, 2)

    # ── Expectancy ────────────────────────────────────────────────────────────
    expectancy_eur  = round(win_rate * avg_win_eur  + (1 - win_rate) * avg_loss_eur,  2)
    expectancy_pips = round(win_rate * avg_win_pips + (1 - win_rate) * avg_loss_pips, 1)

    # ── Avg Trade Length ──────────────────────────────────────────────────────
    durations = [t["duration_sec"] for t in trades if t["duration_sec"] > 0]
    avg_dur   = round(sum(durations) / len(durations)) if durations else 0

    # ── AHPR / GHPR ───────────────────────────────────────────────────────────
    ahpr_returns = []
    running_bal  = balance_start if balance_start > 0 else balance_end
    for t in trades:
        if running_bal > 0:
            ahpr_returns.append(t["pnl_net"] / running_bal)
        running_bal += t["pnl_net"]

    if ahpr_returns:
        ahpr = round(sum(ahpr_returns) / len(ahpr_returns) * 100, 4)
        prod = 1.0
        for r in ahpr_returns:
            prod *= (1 + r)
        ghpr = round((prod ** (1 / len(ahpr_returns)) - 1) * 100, 4)
    else:
        ahpr = ghpr = 0.0

    return {
        "currency":        account.currency,
        "period_days":     days,
        "gain_pct":        round(gain_pct, 2),
        "profit":          round(total_profit, 2),
        "pips":            round(total_pips, 1),
        "win_rate_pct":    round(win_rate * 100, 1),
        "total_trades":    total_trades,
        "total_lots":      round(total_lots, 2),
        "winning_trades":  len(wins),
        "losing_trades":   len(losses),
        "avg_win_eur":     round(avg_win_eur, 2),
        "avg_loss_eur":    round(avg_loss_eur, 2),
        "avg_win_pips":    round(avg_win_pips, 1),
        "avg_loss_pips":   round(avg_loss_pips, 1),
        "longs_total":     len(longs),
        "longs_won":       len(longs_won),
        "longs_win_pct":   round(len(longs_won) / len(longs) * 100, 1) if longs else 0.0,
        "shorts_total":    len(shorts),
        "shorts_won":      len(shorts_won),
        "shorts_win_pct":  round(len(shorts_won) / len(shorts) * 100, 1) if shorts else 0.0,
        "best_trade_eur":   best_t["pnl_net"],
        "best_trade_date":  best_t["close_time"],
        "best_trade_pips":  best_pips_t["pips"],
        "worst_trade_eur":  worst_t["pnl_net"],
        "worst_trade_date": worst_t["close_time"],
        "worst_trade_pips": worst_pips_t["pips"],
        "profit_factor":   profit_factor,
        "std_dev":         std_dev,
        "sharpe_ratio":    sharpe,
        "z_score":         z_score,
        "z_probability":   z_prob,
        "expectancy_eur":  expectancy_eur,
        "expectancy_pips": expectancy_pips,
        "avg_trade_sec":   avg_dur,
        "avg_trade_fmt":   _fmt_duration(avg_dur),
        "ahpr_pct":        ahpr,
        "ghpr_pct":        ghpr,
        "gross_profit":    round(gross_profit, 2),
        "gross_loss":      round(gross_loss, 2),
    }

