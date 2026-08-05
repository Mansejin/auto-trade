"""Compare bull-v2 vs bull ema-di v3 on shared bull path segments."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

OUT = ROOT / "reports" / "bull-entry-v3-20260805"
PATH = ROOT / "reports/five-year/policyC-5y-v2bull-v5sw-path.json"
STRATS = {
    "v2": ROOT / "strategies/regime-bull-trend-4h-v2.json",
    "v3": ROOT / "strategies/regime-bull-trend-4h-ema-di-v3.json",
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
        "win_rate_before_fees_pct": f("win_rate_before_fees_pct"),
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
        pair = {"label": label, "start": start, "end": end}
        for tag, strat in STRATS.items():
            print(f"[{label}] {tag} {start}..{end}", flush=True)
            csv_path = run_bt(strat, start, end)
            dest = OUT / f"{tag}_{label}.csv"
            dest.write_bytes(csv_path.read_bytes())
            perf = parse_perf(dest)
            pair[tag] = {**perf, "csv": str(dest)}
            print(
                f"  {tag}: ret={perf['total_return_pct']} bh={perf['benchmark_pct']} "
                f"mdd={perf['mdd_pct']} pf={perf['profit_factor_before_fees']} n={perf['trades']}",
                flush=True,
            )
        v2, v3 = pair["v2"], pair["v3"]
        if v2["total_return_pct"] is not None and v3["total_return_pct"] is not None:
            pair["d_return_pctp"] = round(v3["total_return_pct"] - v2["total_return_pct"], 4)
            pair["d_mdd_pctp"] = round((v3["mdd_pct"] or 0) - (v2["mdd_pct"] or 0), 4)
            pair["d_bh_gap_pctp"] = round(
                (v3["total_return_pct"] - (v3["benchmark_pct"] or 0))
                - (v2["total_return_pct"] - (v2["benchmark_pct"] or 0)),
                4,
            )
        rows.append(pair)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "generated_at_utc": stamp,
        "hypothesis": "4h EMA golden cross with +DI>-DI and ADX>20 selects continued uptrends more often than golden cross alone.",
        "falsification_criterion": "On fake_jul24/early_cycle: v3 |MDD| not better than v2 by >=1%p; AND on reclaim_nov24/etf_run: v3 BH-gap (ret-bh) worse than v2 by >=5%p → falsified.",
        "rows": rows,
    }
    out = OUT / f"compare-{stamp}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    for r in rows:
        print(
            f"cmp {r['label']}: d_ret={r.get('d_return_pctp')} d_mdd={r.get('d_mdd_pctp')} "
            f"d_bh_gap={r.get('d_bh_gap_pctp')}",
            flush=True,
        )


if __name__ == "__main__":
    main()
