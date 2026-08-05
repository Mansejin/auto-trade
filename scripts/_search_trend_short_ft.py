"""FT trend-short wide+trail grid via in-process FtGrid (fast).

Criteria: PF>=1.2 and trades>=20 on both OOS halves.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ft_bt_fast import ExitParams, FtGrid  # noqa: E402

FT = ROOT / "freqtrade-research"
CFG = FT / "user_data" / "config.bitget-rsi-ichi-check.json"
OUT = ROOT / "reports" / "trend-short-v2-wide-20260805"
WINDOWS = (("h1", "20250901-20260204"), ("h2", "20260204-20260805"))
WORKERS = 4

MODES = ("cloud_break", "di_cloud", "di_only")
ADX_MIN = (20, 25, 30)
RSI_MAX = (50, 55, 60)
SLTP = (
    (-0.010, 0.030),
    (-0.010, 0.040),
    (-0.015, 0.040),
    (-0.015, 0.050),
    (-0.020, 0.050),
    (-0.020, 0.060),
)
def _trail_variants(sl: float, roi: float) -> list[ExitParams]:
    return [
        ExitParams(sl, roi, False),
        ExitParams(sl, roi, True, 0.010, 0.020),
        ExitParams(sl, roi, True, 0.015, 0.030),
    ]


def build_jobs() -> list[dict]:
    jobs: list[dict] = []
    for mode, adx_min, (sl, roi) in product(MODES, ADX_MIN, SLTP):
        # cloud_break ignores adx — keep one adx only
        if mode == "cloud_break" and adx_min != 25:
            continue
        rsi_vals = RSI_MAX if mode == "di_only" else (55,)
        for rsi_max in rsi_vals:
            for ep in _trail_variants(sl, roi):
                tag = (
                    f"{mode}_adx{adx_min}_rsi{rsi_max}"
                    f"_sl{abs(sl)}_tp{roi}"
                    + (f"_tr{ep.trail_pos}_{ep.trail_offset}" if ep.trailing else "_notrail")
                ).replace(".", "p")
                jobs.append(
                    {
                        "tag": tag,
                        "mode": mode,
                        "adx_min": adx_min,
                        "rsi_max": rsi_max,
                        "exit": {
                            "stoploss": ep.stoploss,
                            "roi": ep.roi,
                            "trailing": ep.trailing,
                            "trail_pos": ep.trail_pos,
                            "trail_offset": ep.trail_offset,
                        },
                    }
                )
    # group by entry so advise cache hits inside each worker chunk
    jobs.sort(key=lambda j: (j["mode"], j["adx_min"], j["rsi_max"]))
    return jobs


def _eval_chunk(jobs: list[dict]) -> list[dict]:
    # re-bind imports inside worker (Windows spawn)
    sys.path.insert(0, str(ROOT))
    from scripts.ft_bt_fast import ExitParams as EP, FtGrid as FG

    grids = {name: FG(CFG, "TrendShortV1", tr) for name, tr in WINDOWS}
    rows = []
    for i, job in enumerate(jobs, 1):
        mode, adx, rsi = job["mode"], job["adx_min"], job["rsi_max"]

        def _apply(strat, _mode=mode, _adx=adx, _rsi=rsi):
            strat.entry_mode = _mode
            strat.adx_min = _adx
            strat.rsi_max = _rsi
            return (_mode, _adx, _rsi)

        ep = EP(**job["exit"])
        by = {}
        for name, g in grids.items():
            r = g.run(_apply, ep)
            by[name] = {
                "trades": r.trades,
                "profit_factor": None if r.profit_factor is None else round(r.profit_factor, 4),
                "profit_pct": None if r.profit_pct is None else round(r.profit_pct, 2),
            }
        ok = (
            (by["h1"]["trades"] or 0) >= 20
            and (by["h2"]["trades"] or 0) >= 20
            and (by["h1"]["profit_factor"] or 0) >= 1.2
            and (by["h2"]["profit_factor"] or 0) >= 1.2
        )
        row = {**job, "windows": by, "hit": ok}
        rows.append(row)
        print(
            f"  w[{i}/{len(jobs)}] {job['tag']} "
            f"h1={by['h1'].get('profit_factor')}/{by['h1'].get('trades')} "
            f"h2={by['h2'].get('profit_factor')}/{by['h2'].get('trades')} "
            f"hit={ok}",
            flush=True,
        )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / "results.jsonl"
    done_tags = set()
    cached_rows: list[dict] = []
    if cache.exists():
        for line in cache.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            done_tags.add(row["tag"])
            cached_rows.append(row)

    jobs = [j for j in build_jobs() if j["tag"] not in done_tags]
    print(f"jobs_total={len(build_jobs())} todo={len(jobs)} cached={len(done_tags)} workers={WORKERS}", flush=True)

    rows = list(cached_rows)
    hits = [r for r in rows if r.get("hit")]

    if jobs:
        # split into WORKERS chunks preserving entry locality
        chunks: list[list[dict]] = [[] for _ in range(min(WORKERS, max(1, len(jobs))))]
        for i, j in enumerate(jobs):
            chunks[i % len(chunks)].append(j)
        # re-sort within chunk for advise cache
        for c in chunks:
            c.sort(key=lambda j: (j["mode"], j["adx_min"], j["rsi_max"]))

        with ProcessPoolExecutor(max_workers=len(chunks)) as ex:
            futs = {ex.submit(_eval_chunk, c): i for i, c in enumerate(chunks) if c}
            finished = 0
            for fut in as_completed(futs):
                part = fut.result()
                for row in part:
                    rows.append(row)
                    with cache.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(row) + "\n")
                    finished += 1
                    by = row["windows"]
                    print(
                        f"[{finished}/{len(jobs)}] {row['tag']} "
                        f"h1={by['h1'].get('profit_factor')}/{by['h1'].get('trades')} "
                        f"h2={by['h2'].get('profit_factor')}/{by['h2'].get('trades')} "
                        f"hit={row['hit']}",
                        flush=True,
                    )
                    if row["hit"]:
                        hits.append(row)
                        print("*** HIT", flush=True)

    top = sorted(
        rows,
        key=lambda r: min(
            r["windows"]["h1"].get("profit_factor") or 0,
            r["windows"]["h2"].get("profit_factor") or 0,
        ),
        reverse=True,
    )[:20]
    summary = {
        "criteria": "PF>=1.2 n>=20 both halves",
        "hits": hits,
        "top20": top,
        "n": len(rows),
        "engine": "ft_bt_fast in-process + ProcessPool",
    }
    (OUT / "search-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"hits={len(hits)} best={top[0]['tag'] if top else None}", flush=True)


if __name__ == "__main__":
    # Windows ProcessPool needs guard
    main()
