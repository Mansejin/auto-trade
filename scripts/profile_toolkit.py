"""Profile upbit-strategy-toolkit backtest wall time: spawn vs I/O vs residual.

External wrapper only (does not instrument toolkit). Approximations:
  spawn_floor  = median(uvx ... strategy validate)  # cold-ish process boot
  bt_cold      = backtest --force-refresh
  bt_warm      = same backtest immediately after (cache hit)
  io_approx    = max(0, bt_cold - bt_warm)
  residual     = max(0, bt_warm - spawn_floor)     # compute + CSV + leftover overhead

Usage:
  python scripts/profile_toolkit.py
  python scripts/profile_toolkit.py --strat strategies/regime-bull-trend-4h-v2.json \\
      --start 2024-11-03 --end 2024-12-17 --spawn-runs 3
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UVX_FROM = "git+https://github.com/upbit-official/upbit-strategy-toolkit.git"
TOOL = ["uvx", "--from", UVX_FROM, "upbit-strategy-toolkit"]


def _run(argv: list[str], *, stdin: str | None = None) -> tuple[float, int, str]:
    t0 = time.perf_counter()
    p = subprocess.run(
        argv,
        cwd=ROOT,
        input=stdin,
        capture_output=True,
        text=True,
    )
    dt = time.perf_counter() - t0
    out = (p.stdout or "") + (p.stderr or "")
    return dt, p.returncode, out


def _bt_argv(strat: Path, start: str, end: str, *, force_refresh: bool) -> list[str]:
    cmd = [
        *TOOL,
        "backtest",
        "run",
        str(strat),
        "--start",
        start,
        "--end",
        end,
        "--no-verbose",
    ]
    if force_refresh:
        cmd.append("--force-refresh")
    return cmd


def _maybe_confirm(argv: list[str], stdin: str | None = None) -> tuple[float, int, str]:
    dt, code, out = _run(argv, stdin=stdin)
    if code != 0 and "investment caution" in out.lower():
        dt, code, out = _run(argv, stdin="y\n")
    return dt, code, out


def pct(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return 100.0 * part / total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--strat",
        type=Path,
        default=ROOT / "strategies/regime-bull-trend-4h-v2.json",
    )
    ap.add_argument("--start", default="2024-11-03")
    ap.add_argument("--end", default="2024-12-17")
    ap.add_argument("--spawn-runs", type=int, default=3)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional JSON report path (default reports/toolkit-profile-*.json)",
    )
    args = ap.parse_args()
    strat = args.strat if args.strat.is_absolute() else ROOT / args.strat
    if not strat.exists():
        print(f"missing strategy: {strat}", file=sys.stderr)
        return 1

    print("=== toolkit wall profile ===", flush=True)
    print(f"strat={strat.relative_to(ROOT)}  window={args.start}..{args.end}", flush=True)

    # 1) spawn floor
    validate_cmd = [*TOOL, "strategy", "validate", str(strat)]
    spawn_samples: list[float] = []
    print(f"\n[1] spawn floor  x{args.spawn_runs}  (strategy validate)", flush=True)
    for i in range(args.spawn_runs):
        dt, code, out = _run(validate_cmd)
        spawn_samples.append(dt)
        status = "ok" if code == 0 else f"fail/{code}"
        print(f"  spawn[{i+1}] {dt:.3f}s  {status}", flush=True)
        if code != 0:
            print(out[-500:], file=sys.stderr)
            return code
    spawn_floor = statistics.median(spawn_samples)

    # 2) cold BT
    print("\n[2] backtest COLD (--force-refresh)", flush=True)
    cold_cmd = _bt_argv(strat, args.start, args.end, force_refresh=True)
    t_cold, code, out = _maybe_confirm(cold_cmd)
    print(f"  cold {t_cold:.3f}s  exit={code}", flush=True)
    if code != 0:
        print(out[-800:], file=sys.stderr)
        return code

    # 3) warm BT
    print("\n[3] backtest WARM (cache)", flush=True)
    warm_cmd = _bt_argv(strat, args.start, args.end, force_refresh=False)
    t_warm, code, out = _maybe_confirm(warm_cmd)
    print(f"  warm {t_warm:.3f}s  exit={code}", flush=True)
    if code != 0:
        print(out[-800:], file=sys.stderr)
        return code

    io_approx = max(0.0, t_cold - t_warm)
    residual = max(0.0, t_warm - spawn_floor)
    # accounting against cold total
    accounted = spawn_floor + io_approx + residual
    # residual may overlap spawn in warm; report both absolute and % of cold
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "strategy": str(strat.relative_to(ROOT)).replace("\\", "/"),
        "start": args.start,
        "end": args.end,
        "spawn_runs": args.spawn_runs,
        "spawn_samples_s": [round(x, 4) for x in spawn_samples],
        "spawn_floor_median_s": round(spawn_floor, 4),
        "bt_cold_s": round(t_cold, 4),
        "bt_warm_s": round(t_warm, 4),
        "io_approx_s": round(io_approx, 4),
        "residual_warm_minus_spawn_s": round(residual, 4),
        "pct_of_cold": {
            "spawn_floor": round(pct(spawn_floor, t_cold), 2),
            "io_approx": round(pct(io_approx, t_cold), 2),
            "residual": round(pct(residual, t_cold), 2),
            "note": "residual = warm - spawn; may double-count spawn vs cold decomposition",
        },
        "method": (
            "spawn=median(validate); io≈cold-warm; residual≈warm-spawn. "
            "Does not cProfile child process."
        ),
    }

    print("\n=== summary (seconds) ===", flush=True)
    print(f"  spawn_floor (median validate): {spawn_floor:8.3f}s  ({pct(spawn_floor, t_cold):5.1f}% of cold)", flush=True)
    print(f"  I/O approx   (cold - warm):    {io_approx:8.3f}s  ({pct(io_approx, t_cold):5.1f}% of cold)", flush=True)
    print(f"  residual     (warm - spawn):   {residual:8.3f}s  ({pct(residual, t_cold):5.1f}% of cold)", flush=True)
    print(f"  bt_cold total:                 {t_cold:8.3f}s", flush=True)
    print(f"  bt_warm total:                 {t_warm:8.3f}s", flush=True)
    print(
        "\nInterpretation: if I/O% or spawn% dominates, C++ strategy loops won't help much; "
        "fix uvx reuse / candle cache / batching first.",
        flush=True,
    )

    out_path = args.out
    if out_path is None:
        out_dir = ROOT / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"toolkit-profile-{summary['generated_at_utc']}.json"
    else:
        out_path = out_path if out_path.is_absolute() else ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
