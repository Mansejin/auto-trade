"""Need A proxy: bull-v2 immediate vs +3d / +7d start after bull regime onset."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

OUT = ROOT / "reports" / "bull-gate-20260805"
STRAT = ROOT / "strategies" / "regime-bull-trend-4h-v2.json"
PATH = ROOT / "reports/five-year/policyC-5y-v2bull-v5sw-path.json"
DELAYS = (0, 3, 7)

# Major reclaim / run-up vs weak/fake candidates from five-year path
PICK = {
    "2021-10-01": "early_cycle",
    "2023-02-18": "reclaim_2023",
    "2023-10-27": "reclaim_oct23",
    "2024-02-12": "etf_run",
    "2024-07-15": "fake_jul24",
    "2024-11-03": "reclaim_nov24",
    "2025-07-12": "recent_mixed",
}


def parse_d(s: str) -> date:
    return date.fromisoformat(s[:10])


def run_bt(start: str, end: str) -> Path:
    return run_backtest(STRAT, start, end)


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


def fnum(d: dict[str, str], key: str) -> float | None:
    v = d.get(key)
    if v is None or v.startswith("N/A"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = json.loads(PATH.read_text(encoding="utf-8"))
    segments = [s for s in path["path"] if s.get("regime") == "bull" and s["start"] in PICK]
    rows = []
    for seg in segments:
        label = PICK[seg["start"]]
        end = seg["end"]
        for delay in DELAYS:
            start_d = parse_d(seg["start"]) + timedelta(days=delay)
            end_d = parse_d(end)
            if (end_d - start_d).days < 10:
                print(f"skip {label} d{delay}: too short", flush=True)
                continue
            start_s, end_s = start_d.isoformat(), end_d.isoformat()
            print(f"[{label}] delay={delay} {start_s}..{end_s}", flush=True)
            csv_path = run_bt(start_s, end_s)
            dest = OUT / f"bull-v2_{label}_d{delay}.csv"
            dest.write_bytes(csv_path.read_bytes())
            perf = parse_perf(dest)
            row = {
                "label": label,
                "regime_start": seg["start"],
                "regime_end": end,
                "delay_days": delay,
                "bt_start": start_s,
                "bt_end": end_s,
                "total_return_pct": fnum(perf, "total_return_pct"),
                "benchmark_pct": fnum(perf, "benchmark_pct"),
                "mdd_pct": fnum(perf, "mdd_pct"),
                "profit_factor_before_fees": fnum(perf, "profit_factor_before_fees"),
                "win_rate_before_fees_pct": fnum(perf, "win_rate_before_fees_pct"),
                "trades": fnum(perf, "trades"),
                "sl_count": fnum(perf, "sl_count"),
                "tp_count": fnum(perf, "tp_count"),
                "sell_count": fnum(perf, "sell_count"),
                "csv": str(dest),
            }
            rows.append(row)
            print(
                f"  ret={row['total_return_pct']} bh={row['benchmark_pct']} "
                f"mdd={row['mdd_pct']} pf={row['profit_factor_before_fees']} n={row['trades']}",
                flush=True,
            )

    # Pairwise deltas vs delay 0
    deltas = []
    by = {}
    for r in rows:
        by.setdefault(r["label"], {})[r["delay_days"]] = r
    for label, m in by.items():
        base = m.get(0)
        if not base:
            continue
        for d in (3, 7):
            alt = m.get(d)
            if not alt:
                continue
            if base["total_return_pct"] is None or alt["total_return_pct"] is None:
                continue
            deltas.append(
                {
                    "label": label,
                    "delay_days": d,
                    "d_return_pctp": round(alt["total_return_pct"] - base["total_return_pct"], 4),
                    "d_mdd_pctp": round(
                        (alt["mdd_pct"] or 0) - (base["mdd_pct"] or 0), 4
                    ),
                    "d_vs_bh_pctp": round(
                        (alt["total_return_pct"] - (alt["benchmark_pct"] or 0))
                        - (base["total_return_pct"] - (base["benchmark_pct"] or 0)),
                        4,
                    ),
                    "imm_ret": base["total_return_pct"],
                    "del_ret": alt["total_return_pct"],
                    "imm_mdd": base["mdd_pct"],
                    "del_mdd": alt["mdd_pct"],
                }
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    payload = {
        "generated_at_utc": stamp,
        "hypothesis": "Delaying bull-v2 start by 3d/7d after bull regime onset (G1 proxy) cuts fake-reclaim damage without large return give-up vs immediate.",
        "falsification_criterion": "Across windows with imm trades>=3: median(d_return for delay=3) < -3.0%p AND median(|del_mdd|-|imm_mdd|) does not improve by >=1.0%p (MDD less negative = improve).",
        "strategy": str(STRAT.relative_to(ROOT)),
        "rows": rows,
        "deltas_vs_immediate": deltas,
    }
    out = OUT / f"bull-gate-{stamp}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)
    for d in deltas:
        print(
            f"delta {d['label']} d{d['delay_days']}: ret {d['d_return_pctp']:+}%p "
            f"mdd {d['d_mdd_pctp']:+}%p",
            flush=True,
        )


if __name__ == "__main__":
    main()
