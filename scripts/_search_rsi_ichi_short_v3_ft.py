"""Broader FT true-short search for RSI+ichi v3; stop on PF>=1.2 both halves."""
from __future__ import annotations

import json
import re
import subprocess
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "freqtrade-research"
CFG = FT / "user_data" / "config.bitget-rsi-ichi-check.json"
STRAT = FT / "user_data" / "strategies" / "RsiIchiScalpShortV3.py"
OUT = ROOT / "reports" / "rsi-ichi-short-v3-20260805"

WINDOWS = [("h1", "20250901-20260204"), ("h2", "20260204-20260805")]
# keep full optional for winners only

RSI = (68, 70, 72)
MODES = ("fade_below", "fade_not_above", "level_below")
ADX = ("off", "lt30", "gte25")
SLTP = (
    (-0.003, 0.008),
    (-0.003, 0.012),
    (-0.004, 0.012),
    (-0.005, 0.015),
    (-0.004, 0.016),
)


def patch(rsi: int, mode: str, adx: str, sl: float, roi: float) -> None:
    text = STRAT.read_text(encoding="utf-8")
    text = re.sub(r"stoploss = -0\.\d+", f"stoploss = {sl}", text, count=1)
    text = re.sub(
        r'minimal_roi = \{"0": 0\.\d+\}',
        f'minimal_roi = {{"0": {roi}}}',
        text,
        count=1,
    )
    text = re.sub(r"rsi_thr = \d+", f"rsi_thr = {rsi}", text, count=1)
    text = re.sub(
        r'entry_mode = "[^"]+"',
        f'entry_mode = "{mode}"',
        text,
        count=1,
    )
    text = re.sub(r'adx_mode = "[^"]+"', f'adx_mode = "{adx}"', text, count=1)
    STRAT.write_text(text, encoding="utf-8")


def run_bt(timerange: str) -> str:
    p = subprocess.run(
        [
            str(FT / ".venv" / "Scripts" / "freqtrade.exe"),
            "backtesting",
            "--config",
            str(CFG),
            "--strategy",
            "RsiIchiScalpShortV3",
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
    cfg["strategy"] = "RsiIchiScalpShortV3"
    CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    combos = list(product(RSI, MODES, ADX, SLTP))
    # prioritize likely ones first
    combos.sort(
        key=lambda c: (
            0 if c[1] == "fade_below" else 1,
            0 if c[2] == "lt30" else 1,
            abs(c[0] - 68),
        )
    )
    print(f"combos={len(combos)}", flush=True)

    rows = []
    hits = []
    for i, (rsi, mode, adx, (sl, roi)) in enumerate(combos, 1):
        tag = f"r{rsi}_{mode}_{adx}_sl{abs(sl)}_tp{roi}".replace(".", "p")
        patch(rsi, mode, adx, sl, roi)
        by_w = {}
        for wlabel, tr in WINDOWS:
            text = run_bt(tr)
            met = parse(text)
            by_w[wlabel] = met
        row = {"tag": tag, "rsi": rsi, "mode": mode, "adx": adx, "sl": sl, "roi": roi, "windows": by_w}
        h1, h2 = by_w["h1"], by_w["h2"]
        ok = (
            (h1.get("trades") or 0) >= 20
            and (h2.get("trades") or 0) >= 20
            and (h1.get("profit_factor") or 0) >= 1.2
            and (h2.get("profit_factor") or 0) >= 1.2
        )
        row["hit"] = ok
        rows.append(row)
        print(
            f"[{i}/{len(combos)}] {tag} h1={h1.get('profit_factor')}/{h1.get('trades')} "
            f"h2={h2.get('profit_factor')}/{h2.get('trades')} hit={ok}",
            flush=True,
        )
        if ok:
            hits.append(row)
            (OUT / f"{tag}_h1.txt").write_text(run_bt(WINDOWS[0][1]), encoding="utf-8")
            (OUT / f"{tag}_h2.txt").write_text(run_bt(WINDOWS[1][1]), encoding="utf-8")
            print("*** HIT — stopping", flush=True)
            break
        # early dump every 20
        if i % 20 == 0:
            _dump(rows, hits)

    _dump(rows, hits)
    if not hits and rows:
        def score(r):
            return min(r["windows"]["h1"].get("profit_factor") or 0, r["windows"]["h2"].get("profit_factor") or 0)

        best = max(rows, key=score)
        print(f"best_nonhit {best['tag']} score={score(best)}", flush=True)


def _dump(rows, hits) -> None:
    top = sorted(
        rows,
        key=lambda r: min(
            r["windows"]["h1"].get("profit_factor") or 0,
            r["windows"]["h2"].get("profit_factor") or 0,
        ),
        reverse=True,
    )[:15]
    payload = {
        "criteria": "PF>=1.2 and n>=20 on both halves (true Bitget short)",
        "hits": hits,
        "top15_by_min_half_pf": top,
        "n_eval": len(rows),
    }
    (OUT / "search-summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
