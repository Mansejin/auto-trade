#!/usr/bin/env python3
"""Build Policy C continuous daily equity from per-segment toolkit backtests.

Chains the LIVE map (bull-v2 / m5-v6 / sw-v5) over five-year path segments,
marks open positions on daily closes, compounds across regime switches
(flatten implied by each segment BT end).

Compares MDD/return to lump-sum 50:50 / 80:20 rebalance and 100% BTC hold.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.bt_btc_cash_5050_rebalance import (  # noqa: E402
    INITIAL_KRW,
    Book,
    buy_btc,
    fetch_days,
    mdd,
    parse_d,
    rebalance_to_target,
)
from scripts.toolkit_bt import run_backtest  # noqa: E402

PATH_JSON = ROOT / "reports/five-year/policyC-5y-v2bull-v5sw-path.json"
CACHE = ROOT / "reports/five-year/segment-csv-cache"
OUT = ROOT / "reports"
START = date(2021, 7, 27)
END = date(2026, 7, 26)


def run_segment_bt(strat: str, start: str, end: str) -> Path:
    return run_backtest(strat, start, end, cache_dir=CACHE)

def parse_trades(csv_path: Path) -> list[dict]:
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_trades = False
    rows: list[dict] = []
    header: list[str] | None = None
    for line in lines:
        if line.startswith("# section: trades"):
            in_trades = True
            header = None
            continue
        if in_trades and line.startswith("# section:"):
            break
        if not in_trades or not line.strip():
            continue
        if header is None:
            header = next(csv.reader([line]))
            continue
        vals = next(csv.reader([line]))
        rows.append(dict(zip(header, vals)))
    return rows


def parse_perf(csv_path: Path) -> dict[str, str]:
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_perf = False
    out: dict[str, str] = {}
    for line in lines:
        if line.startswith("# section: performance"):
            in_perf = True
            continue
        if in_perf and line.startswith("# section:"):
            break
        if not in_perf or line.startswith("metric") or not line.strip():
            continue
        k, v = line.split(",", 1)
        out[k] = v
    return out


def _dt(s: str) -> datetime:
    # 2021-08-05 20:00:00 UTC
    return datetime.strptime(s.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )


def segment_daily_equity(
    trades: list[dict],
    days: list[tuple[date, float]],
    start_eq: float,
) -> list[tuple[date, float]]:
    """Mark-to-market daily inside segment; cash when flat. Starts at start_eq."""
    if not days:
        return []
    cash = start_eq
    btc = 0.0
    entry_px = 0.0
    # events by date
    events: dict[date, list[tuple[str, dict]]] = {}
    for t in trades:
        ed = _dt(t["entry_dt"]).date()
        xd = _dt(t["exit_dt"]).date()
        events.setdefault(ed, []).append(("entry", t))
        events.setdefault(xd, []).append(("exit", t))

    # process order: on a day, exits before entries (conservative)
    curve: list[tuple[date, float]] = []
    open_trade: dict | None = None

    for d, px in days:
        for kind, t in sorted(events.get(d, []), key=lambda x: 0 if x[0] == "exit" else 1):
            if kind == "exit" and open_trade is not None:
                # close at trade exit price (realized), not day px — matches BT
                exit_px = float(t["exit_price"])
                # approximate fee already in pnl; use qty * exit and scale to match pnl_pct
                pnl_pct = float(t["pnl_pct"]) / 100.0
                # position notional at entry was cash deployed
                # simpler: equity jumps by pnl on the open stake
                stake = btc * entry_px  # approx pre-fee
                cash = cash + btc * exit_px  # raw
                # force match toolkit trade pnl on the stake we tracked
                # reset via: cash_after = cash_before_entry * (1+pnl) when fully invested
                # We track fully invested per trade (all cash in):
                cash = (cash - btc * exit_px) + stake * (1.0 + pnl_pct)
                # wait - cash before exit included leftover. Model all-in per trade:
                btc = 0.0
                open_trade = None
                entry_px = 0.0
            elif kind == "entry" and open_trade is None:
                open_trade = t
                entry_px = float(t["entry_price"])
                # all-in
                btc = cash / entry_px
                cash = 0.0
        eq = cash + btc * px
        curve.append((d, eq))
    # if still open at segment end, mark at last px (final_bar style)
    return curve


def segment_daily_equity_v2(
    trades: list[dict],
    days: list[tuple[date, float]],
    start_eq: float,
    expected_end_mult: float,
) -> list[tuple[date, float]]:
    """All-in per trade; flat cash between. Scale path so end matches toolkit total return."""
    if not days:
        return []
    # Build unit path starting at 1.0
    eq = 1.0
    curve_u: list[float] = []
    trade_i = 0
    # active trade index
    active: dict | None = None

    # index trades
    tlist = [
        {
            "entry_d": _dt(t["entry_dt"]).date(),
            "exit_d": _dt(t["exit_dt"]).date(),
            "entry_px": float(t["entry_price"]),
            "exit_px": float(t["exit_price"]),
            "pnl_pct": float(t["pnl_pct"]) / 100.0,
        }
        for t in trades
    ]
    tlist.sort(key=lambda x: (x["entry_d"], x["exit_d"]))

    for d, px in days:
        # close?
        if active and d >= active["exit_d"]:
            eq *= 1.0 + active["pnl_pct"]
            active = None
        # open? (only if flat)
        while tlist and tlist[0]["entry_d"] <= d and active is None:
            # skip if this trade already exited before d (shouldn't)
            cand = tlist.pop(0)
            if cand["exit_d"] < d:
                eq *= 1.0 + cand["pnl_pct"]
                continue
            active = cand
            break
        if active:
            # mark from entry
            mark = eq * (px / active["entry_px"])
            # don't update eq until exit; curve uses mark
            curve_u.append(mark)
        else:
            curve_u.append(eq)

    if active:
        # force close with trade pnl at end
        eq *= 1.0 + active["pnl_pct"]
        curve_u[-1] = eq
        active = None

    # any remaining trades (exit after last day) — apply realized
    for cand in tlist:
        eq *= 1.0 + cand["pnl_pct"]
    if curve_u:
        curve_u[-1] = eq

    # scale so final matches toolkit expected_end_mult (1+total_return)
    raw_end = curve_u[-1] if curve_u else 1.0
    if raw_end <= 0:
        scale = start_eq
        return [(d, start_eq) for d, _ in days]
    # prefer matching toolkit total return on endpoint
    target_end = start_eq * expected_end_mult
    # affine scale of entire path around start
    # path_i' = start_eq * (1 + (u_i - 1) / (raw_end - 1) * (expected_end_mult - 1)) if raw_end!=1
    if abs(raw_end - 1.0) < 1e-12:
        return [(d, start_eq) for d, _ in days]
    out: list[tuple[date, float]] = []
    for (d, _), u in zip(days, curve_u):
        # map unit return path to target end return, preserving shape
        frac = (u - 1.0) / (raw_end - 1.0)
        out.append((d, start_eq * (1.0 + frac * (expected_end_mult - 1.0))))
    # ensure end exact
    out[-1] = (out[-1][0], target_end)
    return out


def run_lump(days, *, target, band, cooldown_days, do_rebalance, all_in_btc):
    d0, px0 = days[0]
    book = Book(0.0, 0.0, 0.0, 0.0, 0, None)
    book.cash += INITIAL_KRW
    book.contributed += INITIAL_KRW
    if all_in_btc:
        buy_btc(book, INITIAL_KRW, px0)
    else:
        buy_btc(book, INITIAL_KRW * target, px0)
    series: list[float] = []
    curve: list[tuple[date, float]] = []
    for d, px in days:
        if do_rebalance and not all_in_btc:
            w = book.w_btc(px)
            cooled = book.last_rebal is None or (d - book.last_rebal).days >= cooldown_days
            if cooled and (w > target + band or w < target - band):
                rebalance_to_target(book, px, d, target)
        eq = book.equity(px)
        series.append(eq)
        curve.append((d, eq))
    return {
        "pnl_pct": series[-1] / INITIAL_KRW - 1.0,
        "multiple": series[-1] / INITIAL_KRW,
        "mdd": mdd(series),
        "curve": curve,
    }


def main() -> None:
    path = json.loads(PATH_JSON.read_text(encoding="utf-8"))
    raw = fetch_days(want=2200)
    by_day = {
        parse_d(c["candle_date_time_utc"]): float(c["trade_price"])
        for c in raw
        if START <= parse_d(c["candle_date_time_utc"]) <= END
    }
    all_days = sorted(by_day.items())

    eq = float(INITIAL_KRW)
    continuous: list[tuple[date, float]] = []
    seg_reports = []

    for i, seg in enumerate(path["path"]):
        s, e = seg["start"], seg["end"]
        sd, ed = date.fromisoformat(s), date.fromisoformat(e)
        print(f"[{i+1}/{len(path['path'])}] {seg['regime']} {s}..{e} {seg['file']}", flush=True)
        csv_path = run_segment_bt(seg["file"], s, e)
        trades = parse_trades(csv_path)
        perf = parse_perf(csv_path)
        tr = float(perf.get("total_return_pct", "0").replace("+", "")) / 100.0
        # verify vs path ret
        path_ret = float(seg["ret"]) / 100.0
        days = [(d, px) for d, px in all_days if sd <= d <= ed]
        if not days:
            continue
        expected_mult = 1.0 + path_ret  # use frozen path ret for compound continuity
        # also record toolkit tr for audit
        piece = segment_daily_equity_v2(trades, days, eq, expected_mult)
        # avoid duplicating boundary day: drop first if already in continuous
        if continuous and piece and piece[0][0] == continuous[-1][0]:
            piece = piece[1:]
        continuous.extend(piece)
        if piece:
            eq = piece[-1][1]
        seg_reports.append(
            {
                "start": s,
                "end": e,
                "regime": seg["regime"],
                "n_trades_csv": len(trades),
                "toolkit_total_return": tr,
                "path_ret": path_ret,
                "equity_end": eq,
            }
        )

    series = [v for _, v in continuous]
    pc = {
        "pnl_pct": series[-1] / INITIAL_KRW - 1.0,
        "multiple": series[-1] / INITIAL_KRW,
        "mdd": mdd(series),
        "n_points": len(series),
        "start": continuous[0][0].isoformat(),
        "end": continuous[-1][0].isoformat(),
    }

    # baselines on same calendar
    b = run_lump(all_days, target=0.50, band=0.12, cooldown_days=30, do_rebalance=True, all_in_btc=False)
    c = run_lump(all_days, target=0.80, band=0.10, cooldown_days=14, do_rebalance=True, all_in_btc=False)
    d = run_lump(all_days, target=1.0, band=0.0, cooldown_days=0, do_rebalance=False, all_in_btc=True)

    summary = {
        "period": f"{START} ~ {END}",
        "initial_krw": INITIAL_KRW,
        "method": "policyC_segment_BT_trades_marked_daily_scaled_to_path_ret",
        "A_policyC_continuous": {k: v for k, v in pc.items()},
        "B_50_50_pm12_cd30": {k: v for k, v in b.items() if k != "curve"},
        "C_80_20_pm10_cd14": {k: v for k, v in c.items() if k != "curve"},
        "D_100pct_btc_hold": {k: v for k, v in d.items() if k != "curve"},
        "segments": seg_reports,
        "prior_segment_mark_mdd": -0.1541,
    }

    # write equity csv
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    eq_csv = OUT / f"bt-policyC-continuous-equity-{stamp}.csv"
    with eq_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "equity"])
        for dt, val in continuous:
            w.writerow([dt.isoformat(), f"{val:.4f}"])
    summary_path = OUT / f"bt-fair-race-continuous-{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "segments"}, indent=2))
    print(f"JSON → {summary_path}")
    print(f"CSV  → {eq_csv}")


if __name__ == "__main__":
    main()
