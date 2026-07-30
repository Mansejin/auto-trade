"""Batch OOS backtests for promoted daytrade cards. Stdlib + uvx only."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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

METRICS = [
    ("Benchmark", r"Benchmark\s+([+\-]?\d+\.\d+%)"),
    ("Total Return", r"Total Return\s+([+\-]?\d+\.\d+%)"),
    ("Profit Factor", r"Profit Factor\s+(\S+)"),
    ("Trades", r"Trades\s+(\d+)"),
    ("MDD", r"MDD\s+([+\-]?\d+\.\d+%)"),
    ("Total Fees", r"Total Fees\s+([0-9,]+)"),
]


def parse(stdout: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, pat in METRICS:
        m = re.search(pat, stdout)
        out[key] = m.group(1) if m else "N/A"
    return out


def run_one(slug: str, start: str, end: str) -> dict:
    path = ROOT / "strategies" / f"{slug}.json"
    cmd = [
        "uvx",
        "--from",
        "git+https://github.com/upbit-official/upbit-strategy-toolkit.git",
        "upbit-strategy-toolkit",
        "backtest",
        "run",
        str(path),
        "--start",
        start,
        "--end",
        end,
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    row = {
        "slug": slug,
        "start": start,
        "end": end,
        "exit": proc.returncode,
        **parse(stdout),
    }
    for k, v in list(row.items()):
        if isinstance(v, str):
            row[k] = v.replace("\u221e", "inf").replace("\ufffd", "?")
    if proc.returncode != 0:
        row["error"] = (stderr or stdout)[-400:].encode("ascii", "replace").decode("ascii")
    return row


def main() -> int:
    rows = []
    for slug in STRATEGIES:
        for label, start, end in WINDOWS:
            print(f"RUN {slug} {label} {start}..{end}", flush=True)
            row = run_one(slug, start, end)
            row["window"] = label
            rows.append(row)
            line = (
                f"  ret={row.get('Total Return')} pf={row.get('Profit Factor')} "
                f"trades={row.get('Trades')} bench={row.get('Benchmark')} exit={row['exit']}"
            )
            print(line.encode("ascii", "replace").decode("ascii"), flush=True)

    out_dir = ROOT / "reports" / "automation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "oos-validate-20260730.json"
    out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # markdown summary
    md = ["# OOS validation — promoted daytrade cards", "", "Windows: Feb / Mar / Apr 2026 (~30d each). Promo windows were May–Jul.", ""]
    md.append("| slug | window | return | PF | trades | bench | MDD |")
    md.append("|---|---|---|---|---|---|---|")
    for r in rows:
        md.append(
            f"| `{r['slug']}` | {r['window']} {r['start']}–{r['end']} | "
            f"{r.get('Total Return')} | {r.get('Profit Factor')} | {r.get('Trades')} | "
            f"{r.get('Benchmark')} | {r.get('MDD')} |"
        )
    md.append("")
    md.append("Fees on (toolkit default). Slippage/liquidity not modeled.")
    md_path = out_dir / "oos-validate-20260730.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"WROTE {out_path}")
    print(f"WROTE {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
