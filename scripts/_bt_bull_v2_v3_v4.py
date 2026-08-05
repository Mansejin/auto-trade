"""Compare bull-v2 / ema-di-v3 / ema-di-v4 on shared bull path segments."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

OUT = ROOT / "reports" / "bull-entry-v4-20260805"
PATH = ROOT / "reports/five-year/policyC-5y-v2bull-v5sw-path.json"
STRATS = {
    "v2": ROOT / "strategies/regime-bull-trend-4h-v2.json",
    "v3": ROOT / "strategies/regime-bull-trend-4h-ema-di-v3.json",
    "v4": ROOT / "strategies/regime-bull-trend-4h-ema-di-v4.json",
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
        "trades": f("trades"),
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
            # reuse prior CSVs when present to save time
            cached = OUT / f"{tag}_{label}.csv"
            parent_v3 = ROOT / "reports/bull-entry-v3-20260805" / f"{tag}_{label}.csv"
            if tag in ("v2", "v3") and parent_v3.exists() and not cached.exists():
                cached.write_bytes(parent_v3.read_bytes())
            if cached.exists() and tag != "v4":
                csv_path = cached
                print(f"[{label}] {tag} cache", flush=True)
            else:
                print(f"[{label}] {tag} {start}..{end}", flush=True)
                csv_path = run_bt(strat, start, end)
                cached.write_bytes(csv_path.read_bytes())
            perf = parse_perf(cached)
            pair[tag] = perf
            print(
                f"  {tag}: ret={perf['total_return_pct']} bh={perf['benchmark_pct']} "
                f"mdd={perf['mdd_pct']} n={perf['trades']}",
                flush=True,
            )
        v2, v4 = pair["v2"], pair["v4"]
        if v2["total_return_pct"] is not None and v4["total_return_pct"] is not None:
            pair["v4_minus_v2_ret"] = round(v4["total_return_pct"] - v2["total_return_pct"], 4)
            pair["v4_minus_v2_mdd"] = round((v4["mdd_pct"] or 0) - (v2["mdd_pct"] or 0), 4)
            pair["v4_minus_v2_bh_gap"] = round(
                (v4["total_return_pct"] - (v4["benchmark_pct"] or 0))
                - (v2["total_return_pct"] - (v2["benchmark_pct"] or 0)),
                4,
            )
        rows.append(pair)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "generated_at_utc": stamp,
        "hypothesis": "EMA golden cross with only +DI>-DI (no ADX floor) filters chops better than v2 without v3's major-bull give-up.",
        "falsification_criterion": "On reclaim_nov24 OR etf_run: v4 BH-gap (ret-bh) worse than v2 by >=5%p → falsified. Retained if those two are within 5%p and early_cycle |MDD| improves vs v2 by >=1%p.",
        "rows": rows,
    }
    out = OUT / f"compare-{stamp}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    for r in rows:
        print(
            f"cmp {r['label']}: v4-v2 ret={r.get('v4_minus_v2_ret')} mdd={r.get('v4_minus_v2_mdd')} "
            f"bh_gap={r.get('v4_minus_v2_bh_gap')}",
            flush=True,
        )


if __name__ == "__main__":
    main()
