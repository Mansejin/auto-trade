"""Grid a few true-short RSI+ichi variants on Bitget FT; require PF>=1.2 both halves."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "freqtrade-research"
CFG = FT / "user_data" / "config.bitget-rsi-ichi-check.json"
STRAT_PATH = FT / "user_data" / "strategies" / "RsiIchiScalpShortV2.py"
OUT = ROOT / "reports" / "rsi-ichi-short-v2-20260805"

WINDOWS = [
    ("h1", "20250901-20260204"),
    ("h2", "20260204-20260805"),
    ("full", "20250901-20260805"),
]

# (rsi_thr, stoploss, roi)
GRID = [
    (68, -0.003, 0.008),
    (70, -0.003, 0.008),
    (65, -0.003, 0.008),
    (68, -0.004, 0.010),
    (70, -0.004, 0.012),
    (72, -0.003, 0.009),
    (68, -0.005, 0.015),
    (65, -0.004, 0.010),
]


def patch_strat(rsi: int, sl: float, roi: float) -> None:
    text = STRAT_PATH.read_text(encoding="utf-8")
    text = re.sub(r"stoploss = -0\.\d+", f"stoploss = {sl}", text, count=1)
    text = re.sub(
        r'minimal_roi = \{"0": 0\.\d+\}',
        f'minimal_roi = {{"0": {roi}}}',
        text,
        count=1,
    )
    text = re.sub(r"rsi_thr = \d+", f"rsi_thr = {rsi}", text, count=1)
    STRAT_PATH.write_text(text, encoding="utf-8")


def run_bt(timerange: str) -> str:
    p = subprocess.run(
        [
            str(FT / ".venv" / "Scripts" / "freqtrade.exe"),
            "backtesting",
            "--config",
            str(CFG),
            "--strategy",
            "RsiIchiScalpShortV2",
            "--timerange",
            timerange,
            "--cache",
            "none",
        ],
        cwd=FT,
        capture_output=True,
        text=True,
    )
    return (p.stdout or "") + "\n" + (p.stderr or "")


def parse_metrics(text: str) -> dict:
    if "No trades made" in text:
        return {"trades": 0, "profit_factor": None, "profit_pct": None, "market_change_pct": None}
    out: dict = {}
    m = re.search(r"Total/Daily Avg Trades\s*\|\s*(\d+)", text)
    out["trades"] = int(m.group(1)) if m else None
    m = re.search(r"Profit factor\s*\|\s*([0-9.]+|nan)", text)
    out["profit_factor"] = None if not m or m.group(1) == "nan" else float(m.group(1))
    m = re.search(r"Total profit %\s*\|\s*([+-]?[0-9.]+)%", text)
    out["profit_pct"] = float(m.group(1)) if m else None
    m = re.search(r"Market change\s*\|\s*([+-]?[0-9.]+)%", text)
    out["market_change_pct"] = float(m.group(1)) if m else None
    m = re.search(r"Long / Short trades\s*\|\s*(\d+)\s*/\s*(\d+)", text)
    if m:
        out["long_trades"] = int(m.group(1))
        out["short_trades"] = int(m.group(2))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # point config at V2
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    cfg["strategy"] = "RsiIchiScalpShortV2"
    cfg["startup_candle_count"] = 80
    CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    rows = []
    hits = []
    for rsi, sl, roi in GRID:
        patch_strat(rsi, sl, roi)
        tag = f"r{rsi}_sl{abs(sl)}_tp{roi}"
        print(f"=== {tag} ===", flush=True)
        by_w = {}
        for wlabel, tr in WINDOWS:
            text = run_bt(tr)
            (OUT / f"{tag}_{wlabel}.txt").write_text(text, encoding="utf-8")
            met = parse_metrics(text)
            by_w[wlabel] = met
            print(
                f"  {wlabel}: n={met.get('trades')} pf={met.get('profit_factor')} "
                f"ret={met.get('profit_pct')}",
                flush=True,
            )
        row = {"tag": tag, "rsi": rsi, "sl": sl, "roi": roi, "windows": by_w}
        rows.append(row)
        h1 = by_w["h1"]
        h2 = by_w["h2"]
        ok = (
            (h1.get("trades") or 0) >= 20
            and (h2.get("trades") or 0) >= 20
            and (h1.get("profit_factor") or 0) >= 1.2
            and (h2.get("profit_factor") or 0) >= 1.2
        )
        row["hit_both_halves"] = ok
        if ok:
            hits.append(row)
            print(f"*** HIT {tag}", flush=True)
            break

    payload = {
        "note": "True Bitget futures short only. Upbit invert proxy discarded.",
        "criteria": "PF>=1.2 and trades>=20 on both h1 and h2",
        "hits": hits,
        "rows": rows,
    }
    out = OUT / "search-summary.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} hits={len(hits)}", flush=True)
    if not hits:
        # keep best by min(h1_pf,h2_pf)
        def score(r):
            p1 = (r["windows"]["h1"].get("profit_factor") or 0)
            p2 = (r["windows"]["h2"].get("profit_factor") or 0)
            return min(p1, p2)

        best = max(rows, key=score) if rows else None
        print(f"best_nonhit={best['tag'] if best else None}", flush=True)


if __name__ == "__main__":
    main()
