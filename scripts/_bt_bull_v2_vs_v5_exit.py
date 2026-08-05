"""Compare bull-v2 vs ema50-exit-v5 on bull path segments (BH gap focus)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

OUT = ROOT / "reports" / "bull-exit-v5-20260805"
PATH = ROOT / "reports/five-year/policyC-5y-v2bull-v5sw-path.json"
STRATS = {
    "v2": ROOT / "strategies/regime-bull-trend-4h-v2.json",
    "v5": ROOT / "strategies/regime-bull-trend-4h-ema50-exit-v5.json",
}
PICK = {
    "2021-10-01": "early_cycle",
    "2023-02-18": "reclaim_2023",
    "2023-10-27": "reclaim_oct23",
    "2024-02-12": "etf_run",
    "2024-07-15": "fake_jul24",
    "2024-11-03": "reclaim_nov24",
    "2025-07-12": "recent_mixed",
}
CACHE_V2 = ROOT / "reports/bull-entry-v3-20260805"


def run_bt(strat: Path, start: str, end: str) -> Path:
    return run_backtest(strat, start, end)


def parse_perf(csv_path: Path) -> dict[str, float | None]:
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_perf = False
    raw: dict[str, str] = {}
    for line in lines:
        if line.startswith("# section: performance"):
            in_perf = True
            continue
        if in_perf and line.startswith("# section:"):
            break
        if not in_perf or line.startswith("metric") or not line.strip():
            continue
        k, v = line.split(",", 1)
        raw[k] = v

    def f(key: str) -> float | None:
        v = raw.get(key)
        if v is None or v.startswith("N/A"):
            return None
        try:
            return float(v)
        except ValueError:
            return None

    return {
        "total_return_pct": f("total_return_pct"),
        "benchmark_pct": f("benchmark_pct"),
        "mdd_pct": f("mdd_pct"),
        "profit_factor_before_fees": f("profit_factor_before_fees"),
        "trades": f("trades"),
        "sl_count": f("sl_count"),
        "tp_count": f("tp_count"),
        "sell_count": f("sell_count"),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = json.loads(PATH.read_text(encoding="utf-8"))
    segs = [s for s in path["path"] if s.get("regime") == "bull" and s["start"] in PICK]
    rows = []
    for seg in segs:
        label = PICK[seg["start"]]
        start, end = seg["start"], seg["end"]
        pair: dict = {"label": label, "start": start, "end": end}
        for tag, strat in STRATS.items():
            dest = OUT / f"{tag}_{label}.csv"
            src_cache = CACHE_V2 / f"v2_{label}.csv"
            if tag == "v2" and src_cache.exists():
                dest.write_bytes(src_cache.read_bytes())
                print(f"[{label}] v2 cache", flush=True)
            else:
                print(f"[{label}] {tag} {start}..{end}", flush=True)
                csv_path = run_bt(strat, start, end)
                dest.write_bytes(csv_path.read_bytes())
            perf = parse_perf(dest)
            pair[tag] = perf
            gap = None
            if perf["total_return_pct"] is not None and perf["benchmark_pct"] is not None:
                gap = round(perf["total_return_pct"] - perf["benchmark_pct"], 4)
            pair[f"{tag}_bh_gap"] = gap
            print(
                f"  {tag}: ret={perf['total_return_pct']} bh={perf['benchmark_pct']} "
                f"gap={gap} mdd={perf['mdd_pct']} n={perf['trades']} "
                f"SL/TP/sell={perf['sl_count']}/{perf['tp_count']}/{perf['sell_count']}",
                flush=True,
            )
        if pair.get("v2_bh_gap") is not None and pair.get("v5_bh_gap") is not None:
            pair["gap_improve_pctp"] = round(pair["v5_bh_gap"] - pair["v2_bh_gap"], 4)
            pair["d_ret"] = round(
                (pair["v5"]["total_return_pct"] or 0) - (pair["v2"]["total_return_pct"] or 0), 4
            )
            pair["d_mdd"] = round((pair["v5"]["mdd_pct"] or 0) - (pair["v2"]["mdd_pct"] or 0), 4)
        rows.append(pair)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "generated_at_utc": stamp,
        "hypothesis": "Keeping v2 entries but selling only on EMA5 cross_below EMA50 narrows BH underperformance on major bulls without much worse fake_jul24 MDD.",
        "falsification_criterion": "Median BH-gap improve (v5_gap - v2_gap) across n>=3 windows < +2%p; OR fake_jul24 |MDD| worsens by >=3%p vs v2 → falsified.",
        "rows": rows,
    }
    out = OUT / f"compare-{stamp}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    for r in rows:
        print(
            f"cmp {r['label']}: gap_improve={r.get('gap_improve_pctp')} "
            f"d_ret={r.get('d_ret')} d_mdd={r.get('d_mdd')}",
            flush=True,
        )


if __name__ == "__main__":
    main()
