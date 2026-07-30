#!/usr/bin/env python3
"""5y backtest: DCA + BTC:KRW 50:50 with ±12%p drift rebalance, 1-month cooldown.

Not investment advice. Fees simplified (Upbit-like 0.05% on BTC notional).
Cash earns 0%. Daily closed KRW-BTC candles from Upbit.
"""
from __future__ import annotations

import csv
import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
FEE = 0.0005  # 0.05% per BTC buy/sell notional
TARGET = 0.50
BAND = 0.12  # ±12 percentage points → trigger outside [0.38, 0.62]
COOLDOWN_DAYS = 30
START = date(2021, 7, 30)
END = date(2026, 7, 30)
INITIAL_KRW = 10_000_000.0
MONTHLY_KRW = 1_000_000.0


def fetch_days(market: str = "KRW-BTC", want: int = 2000) -> list[dict]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = f"https://api.upbit.com/v1/candles/days?market={market}&count=200"
        if to:
            url += f"&to={to}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "bt-5050-rebalance"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.loads(resp.read().decode())
        if not batch:
            break
        rows.extend(batch)
        to = batch[-1]["candle_date_time_utc"]
        time.sleep(0.12)
        if len(batch) < 200:
            break
    by = {c["candle_date_time_utc"][:10]: c for c in rows}
    return [by[k] for k in sorted(by)]


def parse_d(s: str) -> date:
    return date.fromisoformat(s[:10])


@dataclass
class Book:
    btc: float
    cash: float
    contributed: float
    fees: float
    rebalances: int
    last_rebal: date | None

    def equity(self, px: float) -> float:
        return self.btc * px + self.cash

    def w_btc(self, px: float) -> float:
        eq = self.equity(px)
        return (self.btc * px / eq) if eq > 0 else TARGET


def buy_btc(book: Book, krw: float, px: float) -> None:
    if krw <= 0 or px <= 0:
        return
    notional = krw
    fee = notional * FEE
    spend = notional - fee
    book.btc += spend / px
    book.cash -= notional
    book.fees += fee


def sell_btc(book: Book, btc_amt: float, px: float) -> None:
    if btc_amt <= 0 or px <= 0:
        return
    gross = btc_amt * px
    fee = gross * FEE
    book.btc -= btc_amt
    book.cash += gross - fee
    book.fees += fee


def rebalance_to_target(book: Book, px: float, when: date) -> bool:
    eq = book.equity(px)
    if eq <= 0:
        return False
    target_btc_val = eq * TARGET
    cur_btc_val = book.btc * px
    delta = target_btc_val - cur_btc_val
    if abs(delta) < 1.0:
        return False
    if delta > 0:
        # need more BTC: spend cash
        spend = min(delta / (1 - FEE), book.cash)
        buy_btc(book, spend, px)
    else:
        # sell BTC
        sell_btc(book, (-delta) / px, px)
    book.rebalances += 1
    book.last_rebal = when
    return True


def contribute_5050(book: Book, krw: float, px: float) -> None:
    """적립: 납입액을 목표비중으로 즉시 배분 (절반 현금, 절반 BTC 매수)."""
    book.cash += krw
    book.contributed += krw
    buy_btc(book, krw * TARGET, px)


def contribute_btc_only(book: Book, krw: float, px: float) -> None:
    book.cash += krw
    book.contributed += krw
    buy_btc(book, krw, px)


def mdd(curve: list[float]) -> float:
    peak = curve[0]
    worst = 0.0
    for v in curve:
        peak = max(peak, v)
        if peak > 0:
            worst = min(worst, v / peak - 1.0)
    return worst


def run_strategy(
    days: list[tuple[date, float]],
    *,
    do_rebalance: bool,
    all_in_btc: bool,
) -> dict:
    d0, px0 = days[0]
    book = Book(btc=0.0, cash=0.0, contributed=0.0, fees=0.0, rebalances=0, last_rebal=None)
    # initial lump at target (or 100% BTC)
    book.cash += INITIAL_KRW
    book.contributed += INITIAL_KRW
    if all_in_btc:
        buy_btc(book, INITIAL_KRW, px0)
    else:
        buy_btc(book, INITIAL_KRW * TARGET, px0)

    curve: list[tuple[str, float, float, float]] = []
    last_contrib_ym: tuple[int, int] | None = (d0.year, d0.month)
    equity_series: list[float] = []

    for d, px in days:
        ym = (d.year, d.month)
        if ym != last_contrib_ym and d > d0:
            # first day of each new month in sample
            if all_in_btc:
                contribute_btc_only(book, MONTHLY_KRW, px)
            else:
                contribute_5050(book, MONTHLY_KRW, px)
            last_contrib_ym = ym

        if do_rebalance and not all_in_btc:
            w = book.w_btc(px)
            cooled = book.last_rebal is None or (d - book.last_rebal).days >= COOLDOWN_DAYS
            if cooled and (w > TARGET + BAND or w < TARGET - BAND):
                rebalance_to_target(book, px, d)

        eq = book.equity(px)
        equity_series.append(eq)
        curve.append((d.isoformat(), eq, book.w_btc(px), book.cash))

    total_in = book.contributed
    final = equity_series[-1]
    return {
        "final_equity": final,
        "contributed": total_in,
        "multiple_on_contrib": final / total_in if total_in else 0.0,
        "pnl": final - total_in,
        "pnl_pct_on_contrib": (final / total_in - 1.0) if total_in else 0.0,
        "mdd": mdd(equity_series),
        "fees": book.fees,
        "rebalances": book.rebalances,
        "final_w_btc": book.w_btc(days[-1][1]),
        "curve": curve,
    }


def main() -> None:
    raw = fetch_days(want=2200)
    days: list[tuple[date, float]] = []
    for c in raw:
        d = parse_d(c["candle_date_time_utc"])
        if START <= d <= END:
            # drop in-progress today if present; prefer closed
            days.append((d, float(c["trade_price"])))
    # if last bar is today UTC and might be open, keep it — user asked through END
    assert len(days) > 400, f"too few days: {len(days)}"

    strat = run_strategy(days, do_rebalance=True, all_in_btc=False)
    hold50 = run_strategy(days, do_rebalance=False, all_in_btc=False)
    btc100 = run_strategy(days, do_rebalance=False, all_in_btc=True)

    summary = {
        "period": f"{days[0][0]} ~ {days[-1][0]}",
        "n_days": len(days),
        "start_px": days[0][1],
        "end_px": days[-1][1],
        "btc_price_return": days[-1][1] / days[0][1] - 1.0,
        "rules": {
            "target": "BTC:KRW 50:50",
            "band_pp": BAND,
            "trigger": f"w_btc outside [{TARGET - BAND:.2f}, {TARGET + BAND:.2f}]",
            "cooldown_days": COOLDOWN_DAYS,
            "dca": f"initial {INITIAL_KRW:,.0f} KRW + monthly {MONTHLY_KRW:,.0f} KRW at 50:50",
            "fee": FEE,
            "cash_yield": 0.0,
        },
        "strategies": {
            "rebalance_5050": {k: v for k, v in strat.items() if k != "curve"},
            "hold_5050_no_rebal": {k: v for k, v in hold50.items() if k != "curve"},
            "dca_100pct_btc": {k: v for k, v in btc100.items() if k != "curve"},
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = OUT / f"bt-5050-rebalance-5y-{stamp}.json"
    csv_path = OUT / f"bt-5050-rebalance-5y-{stamp}.csv"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "equity", "w_btc", "cash"])
        w.writerows(strat["curve"])

    # self-check: band math
    assert abs((TARGET + BAND) - 0.62) < 1e-9
    assert COOLDOWN_DAYS == 30
    print(json.dumps(summary, indent=2))
    print(f"\nJSON → {json_path}")
    print(f"CSV  → {csv_path}")


if __name__ == "__main__":
    main()
