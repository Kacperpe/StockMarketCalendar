from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.models.trade import Trade


def _safe_div(a: Decimal, b: Decimal) -> Decimal:
    if b == 0:
        return Decimal("0")
    return a / b


def compute_stats_from_closed_trades(trades: list[Trade]) -> dict:
    pnls = [Decimal(t.pnl or 0) - Decimal(t.commission or 0) - Decimal(t.swap or 0) - Decimal(t.fees or 0) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = len(pnls)
    win_count = len(wins)
    loss_count = len(losses)

    gross_profit = sum(wins, Decimal("0"))
    gross_loss_abs = abs(sum(losses, Decimal("0")))
    profit_factor = None if gross_loss_abs == 0 else float(_safe_div(gross_profit, gross_loss_abs))
    avg_win = _safe_div(gross_profit, Decimal(win_count)) if win_count else Decimal("0")
    avg_loss = _safe_div(sum(losses, Decimal("0")), Decimal(loss_count)) if loss_count else Decimal("0")
    expectancy = _safe_div(sum(pnls, Decimal("0")), Decimal(total)) if total else Decimal("0")
    win_rate = float(win_count / total) if total else 0.0

    # Balance-curve based max drawdown fallback (start_balance = 0)
    equity = Decimal("0")
    peak = Decimal("0")
    max_dd = Decimal("0")
    max_w_streak = 0
    max_l_streak = 0
    w_streak = 0
    l_streak = 0
    by_day: dict[date, Decimal] = defaultdict(lambda: Decimal("0"))

    for trade, net in sorted(zip(trades, pnls), key=lambda x: x[0].close_time or x[0].open_time):
        equity += net
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd:
            max_dd = dd

        if net > 0:
            w_streak += 1
            l_streak = 0
            max_w_streak = max(max_w_streak, w_streak)
        elif net < 0:
            l_streak += 1
            w_streak = 0
            max_l_streak = max(max_l_streak, l_streak)

        if trade.close_time:
            by_day[trade.close_time.date()] += net

    best_day = max(by_day.values()) if by_day else None
    worst_day = min(by_day.values()) if by_day else None

    return {
        "win_rate": round(win_rate, 4),
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "best_day": best_day,
        "worst_day": worst_day,
        "max_drawdown": max_dd,
        "total_trades": total,
        "wins": win_count,
        "losses": loss_count,
        "streak_wins": max_w_streak,
        "streak_losses": max_l_streak,
    }

