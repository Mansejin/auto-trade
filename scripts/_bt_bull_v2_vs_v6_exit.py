"""Compare bull-v2 vs sell-suppress-ema50-v6 on bull path segments (BH gap focus)."""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_many  # noqa: E402

OUT = ROOT / "reports" / "bull-exit-v6-20260805"
PATH = ROOT / "reports/five-year/policyC-5y-v2bull-v5sw-path.json"
STRATS = {
    "v2": ROOT / "strategies/regime-bull-trend-4h-v2.json",
    "v6": ROOT / "strategies/regime-bull-trend-4h-sell-suppress-ema50-v6.json",
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
    jobs: list[tuple[Path, str, str]] = []
    meta: list[tuple[str, str, str, str]] = []
    for seg in segs:
        label = PICK[seg["start"]]
        for tag, strat in STRATS.items():
            jobs.append((strat, seg["start"], seg["end"]))
            meta.append((label, tag, seg["start"], seg["end"]))

    print(f"running {len(jobs)} jobs...", flush=True)
    paths = run_many(jobs, workers=4)

    by_label: dict[str, dict] = {}
    for (label, tag, start, end), csv_path in zip(meta, paths):
        dest = OUT / f"{tag}_{label}.csv"
        dest.write_bytes(csv_path.read_bytes())
        perf = parse_perf(dest)
        gap = None
        if perf["total_return_pct"] is not None and perf["benchmark_pct"] is not None:
            gap = round(perf["total_return_pct"] - perf["benchmark_pct"], 4)
        row = by_label.setdefault(label, {"label": label, "start": start, "end": end})
        row[tag] = perf
        row[f"{tag}_bh_gap"] = gap
        print(
            f"[{label}] {tag}: ret={perf['total_return_pct']} bh={perf['benchmark_pct']} "
            f"gap={gap} mdd={perf['mdd_pct']} n={perf['trades']} "
            f"SL/TP/sell={perf['sl_count']}/{perf['tp_count']}/{perf['sell_count']}",
            flush=True,
        )

    rows: list[dict] = []
    improves: list[float] = []
    for seg in segs:
        label = PICK[seg["start"]]
        r = by_label[label]
        if r.get("v2_bh_gap") is not None and r.get("v6_bh_gap") is not None:
            r["gap_improve_pctp"] = round(r["v6_bh_gap"] - r["v2_bh_gap"], 4)
            r["d_ret"] = round(
                (r["v6"]["total_return_pct"] or 0) - (r["v2"]["total_return_pct"] or 0), 4
            )
            r["d_mdd"] = round((r["v6"]["mdd_pct"] or 0) - (r["v2"]["mdd_pct"] or 0), 4)
            improves.append(r["gap_improve_pctp"])
        rows.append(r)
        print(
            f"cmp {label}: gap_improve={r.get('gap_improve_pctp')} "
            f"d_ret={r.get('d_ret')} d_mdd={r.get('d_mdd')}",
            flush=True,
        )

    med = statistics.median(improves) if improves else None
    fake = next((r for r in rows if r["label"] == "fake_jul24"), None)
    falsified = False
    reasons: list[str] = []
    if med is not None and med < 2.0:
        falsified = True
        reasons.append(f"median_gap_improve={med} < +2")
    if fake and fake.get("d_mdd") is not None and (fake["d_mdd"] or 0) <= -3.0:
        falsified = True
        reasons.append(f"fake_jul24 d_mdd={fake['d_mdd']} (<= -3 worsens |MDD|)")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "generated_at_utc": stamp,
        "slug": "regime-bull-trend-4h-sell-suppress-ema50-v6",
        "hypothesis": (
            "While close stays above EMA50, EMA5/20 dead-cross sells are often noise; "
            "gating sell until close < EMA50 reduces BH underperformance on major bulls "
            "without much worse fake_jul24 MDD."
        ),
        "falsification_criterion": (
            "Median BH-gap improve (v6_gap - v2_gap) across n>=3 windows < +2%p; "
            "OR fake_jul24 |MDD| worsens by >=3%p vs v2 (d_mdd <= -3)."
        ),
        "median_gap_improve_pctp": med,
        "falsified": falsified,
        "falsify_reasons": reasons,
        "rows": rows,
    }
    out = OUT / f"compare-{stamp}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("---", flush=True)
    print(f"median_gap_improve={med} falsified={falsified} reasons={reasons}", flush=True)
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
