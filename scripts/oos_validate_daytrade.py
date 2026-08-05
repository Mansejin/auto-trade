"""Batch OOS backtests for promoted daytrade cards — cache + parallel."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.toolkit_bt import run_many  # noqa: E402

STRATEGIES = [
    "daytrade-edge-15m-div-v1",
    "daytrade-edge-15m-div-v3",
    "daytrade-edge-10m-div-v1",
    "daytrade-edge-10m-div-adx-v1",
    "daytrade-edge-10m-div-atr-v1",
]
WINDOWS = [
    ("o1_feb", "2026-02-01", "2026-03-02"),
    ("o2_mar", "2026-03-03", "2026-04-01"),
    ("o3_apr", "2026-04-01", "2026-04-30"),
]


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


def main() -> None:
    jobs = []
    meta = []
    for slug in STRATEGIES:
        for name, start, end in WINDOWS:
            jobs.append((ROOT / "strategies" / f"{slug}.json", start, end))
            meta.append((slug, name, start, end))
    paths = run_many(jobs, workers=4)
    rows = []
    for (slug, wname, start, end), csv_path in zip(meta, paths):
        perf = parse_perf(csv_path)
        rows.append(
            {
                "slug": slug,
                "window": wname,
                "start": start,
                "end": end,
                "benchmark_pct": perf.get("benchmark_pct"),
                "total_return_pct": perf.get("total_return_pct"),
                "profit_factor_before_fees": perf.get("profit_factor_before_fees"),
                "trades": perf.get("trades"),
                "mdd_pct": perf.get("mdd_pct"),
                "csv": str(csv_path),
            }
        )
        print(
            f"{slug} {wname}: ret={perf.get('total_return_pct')} "
            f"bh={perf.get('benchmark_pct')} n={perf.get('trades')}",
            flush=True,
        )
    out = ROOT / "reports" / "oos_daytrade_batch.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
