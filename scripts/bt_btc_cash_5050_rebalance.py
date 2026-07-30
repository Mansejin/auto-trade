#!/usr/bin/env python3
"""5y backtest: DCA + BTC:KRW target-weight drift rebalance.

Variants compared in main():
  A) 50:50 ±12%p, cooldown 30d  (LIVE-aligned baseline)
  B) 70:30 ±10%p, cooldown 14d  (opportunity-cost soften)

Not investment advice. Fee 0.05% on BTC notional. Cash yield 0%.
"""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
FEE = 0.0005
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
            headers={"Accept": "application/json", "User-Agent": "bt-btc-cash-rebalance"},
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
        return (self.btc * px / eq) if eq > 0 else 0.0


def buy_btc(book: Book, krw: float, px: float) -> None:
    if krw <= 0 or px <= 0:
        return
    fee = krw * FEE
    book.btc += (krw - fee) / px
    book.cash -= krw
    book.fees += fee


def sell_btc(book: Book, btc_amt: float, px: float) -> None:
    if btc_amt <= 0 or px <= 0:
        return
    gross = btc_amt * px
    fee = gross * FEE
    book.btc -= btc_amt
    book.cash += gross - fee
    book.fees += fee


def rebalance_to_target(book: Book, px: float, when: date, target: float) -> bool:
    eq = book.equity(px)
    if eq <= 0:
        return False
    delta = eq * target - book.btc * px
    if abs(delta) < 1.0:
        return False
    if delta > 0:
        buy_btc(book, min(delta / (1 - FEE), book.cash), px)
    else:
        sell_btc(book, (-delta) / px, px)
    book.rebalances += 1
    book.last_rebal = when
    return True


def contribute_at_target(book: Book, krw: float, px: float, target: float) -> None:
    book.cash += krw
    book.contributed += krw
    buy_btc(book, krw * target, px)


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
    target: float,
    band: float,
    cooldown_days: int,
    do_rebalance: bool,
    all_in_btc: bool,
) -> dict:
    d0, px0 = days[0]
    book = Book(btc=0.0, cash=0.0, contributed=0.0, fees=0.0, rebalances=0, last_rebal=None)
    book.cash += INITIAL_KRW
    book.contributed += INITIAL_KRW
    if all_in_btc:
        buy_btc(book, INITIAL_KRW, px0)
    else:
        buy_btc(book, INITIAL_KRW * target, px0)

    last_contrib_ym = (d0.year, d0.month)
    equity_series: list[float] = []

    for d, px in days:
        ym = (d.year, d.month)
        if ym != last_contrib_ym and d > d0:
            if all_in_btc:
                contribute_btc_only(book, MONTHLY_KRW, px)
            else:
                contribute_at_target(book, MONTHLY_KRW, px, target)
            last_contrib_ym = ym

        if do_rebalance and not all_in_btc:
            w = book.w_btc(px)
            cooled = book.last_rebal is None or (d - book.last_rebal).days >= cooldown_days
            if cooled and (w > target + band or w < target - band):
                rebalance_to_target(book, px, d, target)

        equity_series.append(book.equity(px))

    total_in = book.contributed
    final = equity_series[-1]
    return {
        "target": target,
        "band": band,
        "cooldown_days": cooldown_days,
        "final_equity": final,
        "contributed": total_in,
        "pnl": final - total_in,
        "pnl_pct_on_contrib": (final / total_in - 1.0) if total_in else 0.0,
        "mdd": mdd(equity_series),
        "fees": book.fees,
        "rebalances": book.rebalances,
        "final_w_btc": book.w_btc(days[-1][1]),
    }


def _slim(r: dict) -> dict:
    return {k: v for k, v in r.items()}


def main() -> None:
    raw = fetch_days(want=2200)
    days = [
        (parse_d(c["candle_date_time_utc"]), float(c["trade_price"]))
        for c in raw
        if START <= parse_d(c["candle_date_time_utc"]) <= END
    ]
    assert len(days) > 400, f"too few days: {len(days)}"

    a = run_strategy(
        days, target=0.50, band=0.12, cooldown_days=30, do_rebalance=True, all_in_btc=False
    )
    b = run_strategy(
        days, target=0.70, band=0.10, cooldown_days=14, do_rebalance=True, all_in_btc=False
    )
    hold70 = run_strategy(
        days, target=0.70, band=0.10, cooldown_days=14, do_rebalance=False, all_in_btc=False
    )
    btc100 = run_strategy(
        days, target=1.0, band=0.0, cooldown_days=0, do_rebalance=False, all_in_btc=True
    )

    # self-check: variant B band edges
    assert abs((0.70 + 0.10) - 0.80) < 1e-9
    assert abs((0.70 - 0.10) - 0.60) < 1e-9

    summary = {
        "period": f"{days[0][0]} ~ {days[-1][0]}",
        "n_days": len(days),
        "start_px": days[0][1],
        "end_px": days[-1][1],
        "btc_price_return": days[-1][1] / days[0][1] - 1.0,
        "dca": f"initial {INITIAL_KRW:,.0f} + monthly {MONTHLY_KRW:,.0f} KRW at target weight",
        "fee": FEE,
        "strategies": {
            "A_50_50_pm12_cd30": _slim(a),
            "B_70_30_pm10_cd14": _slim(b),
            "hold_70_30_no_rebal": _slim(hold70),
            "dca_100pct_btc": _slim(btc100),
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = OUT / f"bt-7030-rebalance-5y-{stamp}.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nJSON → {path}")


if __name__ == "__main__":
    main()
