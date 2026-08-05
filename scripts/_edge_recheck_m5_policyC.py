"""Edge recheck runner: m5-v6 solo windows + Policy C compound (refreshed ends)."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

OUT = ROOT / "reports" / "edge-recheck-20260805"
STRAT = ROOT / "strategies" / "krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json"
END = "2026-08-04"

M5_WINDOWS = [
    ("3m_default", "2026-05-04", END),
    ("headline_refresh", "2026-01-26", END),
    ("1y_refresh", "2025-07-26", END),
    ("early_oos", "2025-07-26", "2026-01-26"),
    ("holdout", "2024-11-03", "2025-04-24"),
    ("shallow_bear", "2024-08-09", "2024-10-03"),
]

PC_WINDOWS = [
    ("headline_refresh", "2026-01-26", END),
    ("1y_refresh", "2025-07-26", END),
]

MAP_FILES = {
    "bull": "strategies/regime-bull-trend-4h-v2.json",
    "transition": "strategies/regime-bull-trend-4h-v2.json",
    "bear": "strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "strategies/regime-sideways-mr-4h-v5.json",
}


def run_bt(strat: Path, start: str, end: str) -> Path:
    return run_backtest(strat, start, end)


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


def run_m5() -> list[dict]:
    rows = []
    for name, start, end in M5_WINDOWS:
        print(f"[m5] {name} {start}..{end}", flush=True)
        csv_path = run_bt(STRAT, start, end)
        dest = OUT / f"m5-v6_{name}.csv"
        dest.write_bytes(csv_path.read_bytes())
        perf = parse_perf(dest)
        row = {"window": name, "start": start, "end": end, "csv": str(dest), **perf}
        rows.append(row)
        print(
            f"  ret={perf.get('total_return_pct')} bh={perf.get('benchmark_pct')} "
            f"pf={perf.get('profit_factor_before_fees')} wr={perf.get('win_rate_before_fees_pct')} "
            f"n={perf.get('trades')} mdd={perf.get('mdd_pct')}",
            flush=True,
        )
    return rows


def run_policy_c() -> list[dict]:
    import scripts.bt_policyC_continuous_equity as pc
    from scripts.bt_btc_cash_5050_rebalance import fetch_days as fetch_bh_days, parse_d
    from scripts.regime_engine_v2 import build_segments, fetch_days

    print("fetching daily candles for Policy C…", flush=True)
    candles = fetch_days(want=2500)
    segs_all, _ = build_segments(candles)
    bh_raw = fetch_bh_days(want=2500)
    bh_by = {parse_d(c["candle_date_time_utc"]): float(c["trade_price"]) for c in bh_raw}

    pc.CACHE = OUT / "pc-segment-cache"
    pc.CACHE.mkdir(parents=True, exist_ok=True)

    rows = []
    for name, w0s, w1s in PC_WINDOWS:
        w0, w1 = parse_d(w0s), parse_d(w1s)
        print(f"[pc] {name} {w0}..{w1}", flush=True)
        segs = []
        for s in segs_all:
            a, b = parse_d(s["start"]), parse_d(s["end"])
            if b < w0 or a > w1:
                continue
            start, end = max(a, w0), min(b, w1)
            if (end - start).days < 5:
                continue
            regime = s["regime"]
            if regime not in MAP_FILES:
                continue
            segs.append(
                {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "regime": regime,
                    "file": MAP_FILES[regime],
                }
            )
        print(f"  segments={len(segs)}", flush=True)

        eq = 1_000_000.0
        curve: list[tuple[date, float]] = []
        seg_summary = []
        for s in segs:
            csv_path = pc.run_segment_bt(s["file"], s["start"], s["end"])
            trades = pc.parse_trades(csv_path)
            perf = parse_perf(csv_path)
            tr = float(perf.get("total_return_pct", "0") or 0)
            days = sorted(
                (d, px)
                for d, px in bh_by.items()
                if parse_d(s["start"]) <= d <= parse_d(s["end"])
            )
            if not days:
                continue
            piece = pc.segment_daily_equity_v2(
                trades, days, eq, expected_end_mult=1.0 + tr / 100.0
            )
            if piece:
                # avoid double-counting join day: drop first if continuity
                if curve and piece[0][0] == curve[-1][0]:
                    piece = piece[1:]
                curve.extend(piece)
                eq = piece[-1][1] if piece else eq
            seg_summary.append(
                {
                    "regime": s["regime"],
                    "start": s["start"],
                    "end": s["end"],
                    "file": Path(s["file"]).name,
                    "total_return_pct": tr,
                    "trades": int(float(perf.get("trades", "0") or 0)),
                    "win_rate_before_fees_pct": perf.get("win_rate_before_fees_pct"),
                    "profit_factor_before_fees": perf.get("profit_factor_before_fees"),
                    "mdd_pct": perf.get("mdd_pct"),
                }
            )

        if not curve:
            rows.append({"window": name, "error": "no curve"})
            continue
        start_eq = curve[0][1]
        end_eq = curve[-1][1]
        total_pct = (end_eq / start_eq - 1.0) * 100.0
        mdd_pct = pc.mdd([e for _, e in curve]) * 100.0
        # B&H over same calendar
        px0 = bh_by.get(w0) or next(px for d, px in sorted(bh_by.items()) if d >= w0)
        px1 = bh_by.get(w1) or next(px for d, px in sorted(bh_by.items(), reverse=True) if d <= w1)
        bh_pct = (px1 / px0 - 1.0) * 100.0
        row = {
            "window": name,
            "start": w0s,
            "end": w1s,
            "segments": len(segs),
            "total_return_pct": round(total_pct, 4),
            "mdd_pct": round(mdd_pct, 4),
            "benchmark_pct": round(bh_pct, 4),
            "segment_details": seg_summary,
        }
        rows.append(row)
        print(
            f"  pc_ret={row['total_return_pct']} bh={row['benchmark_pct']} mdd={row['mdd_pct']}",
            flush=True,
        )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    m5 = run_m5()
    pc = run_policy_c()
    payload = {
        "generated_at_utc": stamp,
        "end_anchor": END,
        "m5_v6": m5,
        "policy_c": pc,
        "note": "Toolkit CSV metrics quoted as-is; Policy C compounds segment BTs.",
    }
    out = OUT / f"edge-recheck-{stamp}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
