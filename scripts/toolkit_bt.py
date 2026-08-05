"""Shared fast toolkit backtest runner: local CLI + disk cache + optional parallel.

Bottleneck profile (see scripts/profile_toolkit.py): most wall time is uvx spawn +
candle fetch. This module:
  1) prefers an already-installed `upbit-strategy-toolkit` (uv tool install)
  2) caches CSV by (stem, start, end) under reports/bt-cache/
  3) can run many jobs concurrently (ProcessPoolExecutor)

Usage:
  from scripts.toolkit_bt import run_backtest, run_many, ensure_toolkit_cli
  csv = run_backtest("strategies/foo.json", "2024-01-01", "2024-06-01")
  paths = run_many([("strategies/a.json", "2024-01-01", "2024-02-01"), ...], workers=4)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UV_FROM = "git+https://github.com/upbit-official/upbit-strategy-toolkit.git"
DEFAULT_CACHE = ROOT / "reports" / "bt-cache"

_CLI: list[str] | None = None


def ensure_toolkit_cli(*, install_if_missing: bool = True) -> list[str]:
    """Return argv prefix for toolkit. Prefer installed tool over uvx --from."""
    global _CLI
    if _CLI is not None:
        return _CLI

    def _find() -> str | None:
        which = shutil.which("upbit-strategy-toolkit")
        if which:
            return which
        # uv tool install often lands here even when not on PATH (esp. Windows)
        for name in ("upbit-strategy-toolkit.exe", "upbit-strategy-toolkit"):
            p = Path.home() / ".local" / "bin" / name
            if p.is_file():
                return str(p)
        return None

    which = _find()
    if which:
        _CLI = [which]
        return _CLI

    uv = shutil.which("uv")
    if install_if_missing and uv:
        subprocess.run(
            [uv, "tool", "install", "--quiet", "--from", UV_FROM, "upbit-strategy-toolkit"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        which = _find()
        if which:
            _CLI = [which]
            return _CLI

    # Fallback: uvx (slower cold start)
    uvx = shutil.which("uvx") or "uvx"
    _CLI = [uvx, "--from", UV_FROM, "upbit-strategy-toolkit"]
    return _CLI


def cache_path(
    strategy: Path | str,
    start: str,
    end: str,
    *,
    cache_dir: Path | None = None,
    fee_rate: float | None = None,
) -> Path:
    stem = Path(strategy).stem
    key = f"{stem}_{start}_{end}".replace(":", "")
    if fee_rate is not None:
        key = f"{key}_fee{fee_rate}"
    return (cache_dir or DEFAULT_CACHE) / f"{key}.csv"


def _resolve_strat(strategy: Path | str) -> Path:
    p = Path(strategy)
    if not p.is_absolute():
        p = ROOT / p
    return p


def _find_new_csv(strat: Path, before: set[Path]) -> Path:
    after = [p for p in (ROOT / "reports").glob("*.csv") if p.resolve() not in before]
    if after:
        return max(after, key=lambda p: p.stat().st_mtime)
    cands = sorted((ROOT / "reports").glob(f"{strat.stem}-*.csv"), key=lambda p: p.stat().st_mtime)
    if not cands:
        raise FileNotFoundError(f"no CSV produced for {strat.name}")
    return cands[-1]


def run_backtest(
    strategy: Path | str,
    start: str,
    end: str,
    *,
    cache_dir: Path | None = None,
    force: bool = False,
    force_refresh_candles: bool = False,
    quiet: bool = True,
    fee_rate: float | None = None,
) -> Path:
    """Run one backtest; return path to cached (or just-written) CSV."""
    strat = _resolve_strat(strategy)
    if not strat.exists():
        raise FileNotFoundError(strat)
    cdir = cache_dir or DEFAULT_CACHE
    cdir.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    dest = cache_path(strat, start, end, cache_dir=cdir, fee_rate=fee_rate)
    if dest.exists() and not force:
        return dest

    cli = ensure_toolkit_cli()
    cmd = [
        *cli,
        "backtest",
        "run",
        str(strat),
        "--start",
        start,
        "--end",
        end,
    ]
    if quiet:
        cmd.append("--no-verbose")
    if force_refresh_candles:
        cmd.append("--force-refresh")
    if fee_rate is not None:
        cmd.extend(["--fee-rate", str(fee_rate)])

    before = {p.resolve() for p in (ROOT / "reports").glob("*.csv")}
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0 and "investment caution" in out.lower():
        p = subprocess.run(cmd, cwd=ROOT, input="y\n", capture_output=True, text=True)
        out = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        raise RuntimeError(f"backtest failed {strat.name} {start}..{end}\n{out[-2000:]}")

    time.sleep(0.05)
    src = _find_new_csv(strat, before)
    dest.write_bytes(src.read_bytes())
    return dest


def _worker(job: tuple[str, str, str, str, bool, bool, float | None]) -> tuple[str, str, str, str]:
    strat_s, start, end, cache_s, force, force_candles, fee = job
    path = run_backtest(
        strat_s,
        start,
        end,
        cache_dir=Path(cache_s),
        force=force,
        force_refresh_candles=force_candles,
        fee_rate=fee,
    )
    return strat_s, start, end, str(path)


def run_many(
    jobs: list[tuple[str | Path, str, str]],
    *,
    workers: int | None = None,
    cache_dir: Path | None = None,
    force: bool = False,
    force_refresh_candles: bool = False,
    fee_rate: float | None = None,
) -> list[Path]:
    """Run many (strategy, start, end) jobs. Uses cache; parallel when workers>1."""
    cdir = cache_dir or DEFAULT_CACHE
    cdir.mkdir(parents=True, exist_ok=True)
    ensure_toolkit_cli()  # warm install once in parent

    normalized: list[tuple[str, str, str, str, bool, bool, float | None]] = []
    for strat, start, end in jobs:
        sp = _resolve_strat(strat)
        normalized.append(
            (str(sp), start, end, str(cdir), force, force_refresh_candles, fee_rate)
        )

    todo = []
    done_map: dict[tuple[str, str, str], Path] = {}
    for job in normalized:
        strat_s, start, end, cache_s, fr, fc, fee = job
        cp = cache_path(strat_s, start, end, cache_dir=Path(cache_s), fee_rate=fee)
        if cp.exists() and not fr:
            done_map[(strat_s, start, end)] = cp
        else:
            todo.append(job)

    if not todo:
        return [done_map[(j[0], j[1], j[2])] for j in normalized]

    n_workers = workers
    if n_workers is None:
        n_workers = min(4, max(1, (os.cpu_count() or 2)))
    n_workers = max(1, min(n_workers, len(todo)))

    if n_workers == 1:
        for job in todo:
            s, a, b, path = _worker(job)
            done_map[(s, a, b)] = Path(path)
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futs = [ex.submit(_worker, job) for job in todo]
            for fut in as_completed(futs):
                s, a, b, path = fut.result()
                done_map[(s, a, b)] = Path(path)

    return [done_map[(j[0], j[1], j[2])] for j in normalized]


if __name__ == "__main__":
    # ponytail: smallest check — CLI resolves and cache key is stable
    cli = ensure_toolkit_cli()
    assert cli, "empty cli"
    p = cache_path("strategies/x.json", "2024-01-01", "2024-02-01")
    assert p.name == "x_2024-01-01_2024-02-01.csv", p.name
    print("ok", "cli0=", Path(cli[0]).name)
