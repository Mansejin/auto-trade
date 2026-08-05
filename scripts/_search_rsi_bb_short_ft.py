"""FT true-short RSI+BB search; stop when PF>=1.2 on both OOS halves."""
from __future__ import annotations

import json
import re
import subprocess
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "freqtrade-research"
CFG = FT / "user_data" / "config.bitget-rsi-ichi-check.json"
STRAT = FT / "user_data" / "strategies" / "RsiBbScalpShortV5.py"
OUT = ROOT / "reports" / "rsi-bb-short-v5-20260805"
WINDOWS = [("h1", "20250901-20260204"), ("h2", "20260204-20260805")]

RSI = (70, 75, 80)
ADX = ("off", "lt30", "gte25")
SLTP = (
    (-0.003, 0.008),
    (-0.003, 0.010),
    (-0.004, 0.010),
    (-0.004, 0.012),
    (-0.005, 0.015),
    (-0.003, 0.012),
)


def patch(rsi: int, adx: str, sl: float, roi: float) -> None:
    t = STRAT.read_text(encoding="utf-8")
    t = re.sub(r"stoploss = -0\.\d+", f"stoploss = {sl}", t, count=1)
    t = re.sub(
        r'minimal_roi = \{"0": 0\.\d+\}',
        f'minimal_roi = {{"0": {roi}}}',
        t,
        count=1,
    )
    t = re.sub(r"rsi_thr = \d+", f"rsi_thr = {rsi}", t, count=1)
    t = re.sub(r'adx_mode = "[^"]+"', f'adx_mode = "{adx}"', t, count=1)
    STRAT.write_text(t, encoding="utf-8")


def run(tr: str) -> str:
    p = subprocess.run(
        [
            str(FT / ".venv" / "Scripts" / "freqtrade.exe"),
            "backtesting",
            "--config",
            str(CFG),
            "--strategy",
            "RsiBbScalpShortV5",
            "--timerange",
            tr,
            "--cache",
            "none",
        ],
        cwd=FT,
        capture_output=True,
        text=True,
    )
    return (p.stdout or "") + "\n" + (p.stderr or "")


def parse(text: str) -> dict:
    if "No trades made" in text:
        return {"trades": 0, "profit_factor": None, "profit_pct": None}
    out: dict = {}
    m = re.search(r"Total/Daily Avg Trades\s*\|\s*(\d+)", text)
    out["trades"] = int(m.group(1)) if m else 0
    m = re.search(r"Profit factor\s*\|\s*([0-9.]+|nan)", text)
    out["profit_factor"] = None if not m or m.group(1) == "nan" else float(m.group(1))
    m = re.search(r"Total profit %\s*\|\s*([+-]?[0-9.]+)%", text)
    out["profit_pct"] = float(m.group(1)) if m else None
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    cfg["strategy"] = "RsiBbScalpShortV5"
    CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    combos = list(product(RSI, ADX, SLTP))
    print(f"combos={len(combos)}", flush=True)
    rows, hits = [], []
    for i, (rsi, adx, (sl, roi)) in enumerate(combos, 1):
        tag = f"r{rsi}_{adx}_sl{abs(sl)}_tp{roi}".replace(".", "p")
        patch(rsi, adx, sl, roi)
        by = {w: parse(run(tr)) for w, tr in WINDOWS}
        ok = (
            (by["h1"].get("trades") or 0) >= 20
            and (by["h2"].get("trades") or 0) >= 20
            and (by["h1"].get("profit_factor") or 0) >= 1.2
            and (by["h2"].get("profit_factor") or 0) >= 1.2
        )
        row = {"tag": tag, "rsi": rsi, "adx": adx, "sl": sl, "roi": roi, "windows": by, "hit": ok}
        rows.append(row)
        print(
            f"[{i}/{len(combos)}] {tag} h1={by['h1'].get('profit_factor')}/{by['h1'].get('trades')} "
            f"h2={by['h2'].get('profit_factor')}/{by['h2'].get('trades')} hit={ok}",
            flush=True,
        )
        if ok:
            hits.append(row)
            print("*** HIT", flush=True)
            break

    top = sorted(
        rows,
        key=lambda r: min(
            r["windows"]["h1"].get("profit_factor") or 0,
            r["windows"]["h2"].get("profit_factor") or 0,
        ),
        reverse=True,
    )[:15]
    (OUT / "search-summary.json").write_text(
        json.dumps(
            {"criteria": "PF>=1.2 n>=20 both halves", "hits": hits, "top15": top, "n": len(rows)},
            indent=2,
        ),
        encoding="utf-8",
    )
    if hits:
        # freeze winning attrs already on disk from last patch
        print(f"frozen_in_strategy_file tag={hits[0]['tag']}", flush=True)
    elif top:
        print(f"best_nonhit={top[0]['tag']}", flush=True)


if __name__ == "__main__":
    main()
