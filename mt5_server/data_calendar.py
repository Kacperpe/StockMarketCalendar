import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from calendar import monthrange
from collections import defaultdict


def get_calendar_data(year: int, month: int) -> dict:
    """
    Zwraca dane do kalendarza miesięcznego:
    {
      "days": {
        "2025-03-02": {"pnl": 385.66, "trades": 8, "wins": 8, "losses": 0, "win_rate": 100.0},
        ...
      },
      "weeks": {
        1: {"pnl": -1496.89, "trading_days": 3},
        ...
      }
    }
    """
    date_from = datetime(year, month, 1)
    if month == 12:
        date_to = datetime(year + 1, 1, 1)
    else:
        date_to = datetime(year, month + 1, 1)

    deals = mt5.history_deals_get(date_from, date_to)
    if not deals:
        return {"days": {}, "weeks": {}}

    rows = []
    for d in deals:
        rows.append({
            "position_id": d.position_id,
            "symbol":      d.symbol,
            "type":        d.type,
            "entry":       d.entry,
            "profit":      d.profit,
            "swap":        d.swap,
            "commission":  d.commission,
            "pnl_net":     d.profit + d.swap + d.commission,
            "time":        datetime.utcfromtimestamp(d.time),
        })

    df = pd.DataFrame(rows)

    # Tylko zamknięcia pozycji (entry == 1) i ruch powrotny CFD (entry == 2)
    exits = df[df["entry"].isin([1, 2])].copy()

    if exits.empty:
        return {"days": {}, "weeks": {}}

    # Agreguj wiele deali tej samej pozycji (np. częściowe zamknięcia)
    trades = exits.groupby("position_id").agg(
        pnl_net=("pnl_net", "sum"),
        close_time=("time", "last"),
    ).reset_index()

    trades["date"] = trades["close_time"].dt.date

    day_data = {}
    for date, group in trades.groupby("date"):
        wins   = int((group["pnl_net"] > 0).sum())
        losses = int((group["pnl_net"] < 0).sum())
        total  = len(group)
        day_data[str(date)] = {
            "pnl":      round(float(group["pnl_net"].sum()), 2),
            "trades":   total,
            "wins":     wins,
            "losses":   losses,
            "win_rate": round(wins / total * 100, 2) if total > 0 else 0.0,
        }

    week_data = _calc_weeks(year, month, day_data)
    return {"days": day_data, "weeks": week_data}


def _calc_weeks(year: int, month: int, day_data: dict) -> dict:
    """
    Dzieli miesiąc na tygodnie dokładnie tak, jak prezentuje Myfxbook:
    każdy rząd siatki kalendarza (Mon–Sun) to jeden tydzień (1–6).
    Tydzień kończy się w niedzielę i zaczyna w poniedziałek.
    """
    _, days_in_month = monthrange(year, month)

    weeks: dict = defaultdict(lambda: {"pnl": 0.0, "trading_days": 0})
    week_num = 1

    for day in range(1, days_in_month + 1):
        from datetime import date as date_cls
        date = date_cls(year, month, day)
        date_str = str(date)

        if date_str in day_data:
            weeks[week_num]["pnl"] += day_data[date_str]["pnl"]
            weeks[week_num]["trading_days"] += 1

        # Niedziela = koniec tygodnia (0=Mon … 6=Sun)
        if date.weekday() == 6:
            week_num += 1

    result = {}
    for wk, data in weeks.items():
        result[wk] = {"pnl": round(data["pnl"], 2), "trading_days": data["trading_days"]}

    return result
