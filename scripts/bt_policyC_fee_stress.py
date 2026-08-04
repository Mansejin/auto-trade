#!/usr/bin/env python3
"""Policy C fee stress (diagnostic): re-run OOS segments at 2× default fee.

Uses frozen OOS segment list from reports/bt-policyC-oos-presample-*.json.
Does NOT retune map. Compares toolkit total_return at fee_rate=0.001 vs baseline
stored toolkit_ret_pct from the OOS run (exchange default ~0.05%).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
CACHE = ROOT / "reports/five-year/segment-csv-cache-fee2x"
STRESS_FEE = 0.001  # 0.10% — ~2× typical Upbit 0.05%


def latest_oos() -> Path:
    cands = sorted(OUT.glob("bt-policyC-oos-presample-20*.json"))
    cands = [p for p in cands if "aligned" not in p.name]
    if not cands:
        raise SystemExit("no OOS presample JSON — run bt_policyC_oos_presample.py first")
    return cands[-1]


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


def run_bt(strat: str, start: str, end: str, fee: float) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = f"{Path(strat).stem}_{start}_{end}_fee{fee}".replace(":", "")
    cached = list(CACHE.glob(f"{key}.csv"))
    if cached:
        return cached[0]
    before = {p.resolve() for p in OUT.glob("*.csv")}
    cmd = [
        "uvx",
        "--from",
        "git+https://github.com/upbit-official/upbit-strategy-toolkit.git",
        "upbit-strategy-toolkit",
        "backtest",
        "run",
        str(ROOT / strat),
        "--start",
        start,
        "--end",
        end,
        "--fee-rate",
        str(fee),
    ]
    subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.25)
    after = [p for p in OUT.glob("*.csv") if p.resolve() not in before]
    stem = Path(strat).stem
    if after:
        src = max(after, key=lambda p: p.stat().st_mtime)
    else:
        cands = sorted(OUT.glob(f"{stem}-*.csv"), key=lambda p: p.stat().st_mtime)
        if not cands:
            raise FileNotFoundError(f"no CSV {strat} {start} {end}")
        src = cands[-1]
    dest = CACHE / f"{key}.csv"
    dest.write_bytes(src.read_bytes())
    return dest


def compound(rets: list[float]) -> float:
    m = 1.0
    for r in rets:
        m *= 1.0 + r
    return m


def main() -> None:
    oos_path = latest_oos()
    oos = json.loads(oos_path.read_text(encoding="utf-8"))
    segs = [s for s in oos["segments"] if "error" not in s and "toolkit_ret_pct" in s]
    print(f"baseline={oos_path.name} n={len(segs)} stress_fee={STRESS_FEE}", flush=True)

    base_rets = []
    stress_rets = []
    rows = []
    for i, seg in enumerate(segs):
        base_r = float(seg["toolkit_ret_pct"]) / 100.0
        print(
            f"[{i+1}/{len(segs)}] {seg['regime']} {seg['start']}→{seg['end']} "
            f"base={base_r*100:+.2f}%",
            flush=True,
        )
        csv_path = run_bt(seg["file"], seg["start"], seg["end"], STRESS_FEE)
        perf = parse_perf(csv_path)
        stress_r = float(str(perf.get("total_return_pct", "0")).replace("+", "")) / 100.0
        base_rets.append(base_r)
        stress_rets.append(stress_r)
        rows.append(
            {
                **{k: seg[k] for k in ("start", "end", "regime", "file", "days")},
                "base_toolkit_ret_pct": round(base_r * 100, 2),
                "stress_toolkit_ret_pct": round(stress_r * 100, 2),
                "delta_pp": round((stress_r - base_r) * 100, 2),
            }
        )
        print(f"  stress={stress_r*100:+.2f}% delta={(stress_r-base_r)*100:+.2f}pp", flush=True)

    base_m = compound(base_rets)
    stress_m = compound(stress_rets)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary = {
        "baseline_oos": str(oos_path.relative_to(ROOT)),
        "aligned_note": oos.get("aligned_window"),
        "stress_fee_rate": STRESS_FEE,
        "baseline_fee_note": "toolkit/exchange default at OOS run (~0.05% Upbit)",
        "n_segments": len(segs),
        "baseline_compound_multiple": round(base_m, 4),
        "baseline_compound_return_pct": round((base_m - 1) * 100, 2),
        "stress_compound_multiple": round(stress_m, 4),
        "stress_compound_return_pct": round((stress_m - 1) * 100, 2),
        "return_haircut_pp": round((stress_m - base_m) * 100, 2),
        "still_positive": stress_m > 1.0,
        "segments": rows,
    }
    out_json = OUT / f"bt-policyC-fee-stress-2x-{stamp}.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md = OUT.parent / "docs" / "research" / "policyC-fee-stress-2x.md"
    # write under docs/research
    md = ROOT / "docs" / "research" / "policyC-fee-stress-2x.md"
    md.write_text(
        "\n".join(
            [
                "# Policy C fee stress (2×) — diagnostic",
                "",
                "> Map frozen. No retune. OOS segment chain only.",
                "",
                f"- Baseline OOS: `{oos_path.name}`",
                f"- Stress fee: **{STRESS_FEE}** (≈2× 0.05%)",
                f"- Segments: {len(segs)}",
                "",
                "| | Baseline (default fee) | Stress 2× fee |",
                "|--|--:|--:|",
                f"| Compound return | **{summary['baseline_compound_return_pct']:+.2f}%** | **{summary['stress_compound_return_pct']:+.2f}%** |",
                f"| Multiple | {summary['baseline_compound_multiple']:.3f}× | {summary['stress_compound_multiple']:.3f}× |",
                f"| Haircut | | {summary['return_haircut_pp']:+.2f} pp |",
                f"| Still profitable? | | **{'YES' if summary['still_positive'] else 'NO'}** |",
                "",
                "## Verdict",
                "",
                (
                    "Fee doubling does not kill the OOS compound path."
                    if summary["still_positive"]
                    else "Fee doubling wiped OOS compound — treat live sizing even more carefully."
                ),
                "",
                f"JSON: `{out_json.relative_to(ROOT)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({k: summary[k] for k in summary if k != "segments"}, indent=2))
    print(f"wrote {out_json}")
    print(f"wrote {md}")


if __name__ == "__main__":
    main()
