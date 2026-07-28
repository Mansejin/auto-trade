#!/usr/bin/env python3
"""Server-side daily regime classifier + STRATEGY_PATH switcher (stdlib only)."""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("AUTO_TRADE_ROOT", str(Path.home() / "auto-trade")))
STRAT_DIR = ROOT / "strategies"
ENV_FILE = ROOT / ".env"
LOG_FILE = ROOT / "logs" / "regime-switch.jsonl"
ACTIVE = STRAT_DIR / "ACTIVE_STRATEGY"

POLICY = {
    "bull": "regime-bull-trend-4h-v2.json",
    "transition": "regime-bull-trend-4h-v2.json",
    "bear": "krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "regime-sideways-mr-4h-v4.json",
}


def fetch_days(want: int = 260) -> list[dict]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = "https://api.upbit.com/v1/candles/days?market=KRW-BTC&count=200"
        if to:
            url += f"&to={to}"
        req = urllib.request.Request(
            url, headers={"Accept": "application/json", "User-Agent": "regime-switch-server"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.loads(resp.read().decode())
        if not batch:
            break
        rows.extend(batch)
        to = batch[-1]["candle_date_time_utc"]
        time.sleep(0.12)
        if len(batch) < 200:
            break
    by = {c["candle_date_time_utc"][:10]: c for c in rows}
    return [by[k] for k in sorted(by)]


def sma(arr: list[float], p: int, i: int):
    if i + 1 < p:
        return None
    return sum(arr[i + 1 - p : i + 1]) / p


def adx_last(highs, lows, closes, period: int = 14):
    n = len(closes)
    tr = [None] * n
    plus_dm = [None] * n
    minus_dm = [None] * n
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        plus_dm[i] = up if up > dn and up > 0 else 0.0
        minus_dm[i] = dn if dn > up and dn > 0 else 0.0

    def wilder(vals, p):
        out = [None] * n
        out[p] = sum(vals[1 : p + 1])
        for i in range(p + 1, n):
            out[i] = out[i - 1] - out[i - 1] / p + vals[i]
        return out

    atr = wilder(tr, period)
    pdm = wilder(plus_dm, period)
    mdm = wilder(minus_dm, period)
    pdi = [None] * n
    mdi = [None] * n
    dx = [None] * n
    adx = [None] * n
    for i in range(n):
        if atr[i] and atr[i] != 0 and pdm[i] is not None:
            pdi[i] = 100 * pdm[i] / atr[i]
            mdi[i] = 100 * mdm[i] / atr[i]
            denom = pdi[i] + mdi[i]
            dx[i] = 100 * abs(pdi[i] - mdi[i]) / denom if denom else 0.0
    start = period * 2
    adx[start] = sum(dx[i] for i in range(period, start + 1)) / period
    for i in range(start + 1, n):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period
    return pdi[-1], mdi[-1], adx[-1]


def classify(candles: list[dict]) -> dict:
    closes = [c["trade_price"] for c in candles]
    highs = [c["high_price"] for c in candles]
    lows = [c["low_price"] for c in candles]
    i = len(closes) - 1
    s50 = sma(closes, 50, i)
    s200 = sma(closes, 200, i)
    pdi, mdi, adx = adx_last(highs, lows, closes)
    if None in (s50, s200, adx, pdi, mdi):
        raise RuntimeError("insufficient candles")
    if adx < 20:
        regime = "sideways"
    elif closes[i] > s200 and s50 > s200 and pdi >= mdi:
        regime = "bull"
    elif closes[i] < s200 and s50 < s200 and closes[i] < s50 and mdi > pdi:
        regime = "bear"
    else:
        regime = "transition"
    return {
        "date": candles[i]["candle_date_time_utc"][:10],
        "regime": regime,
        "close": closes[i],
        "sma50": s50,
        "sma200": s200,
        "adx": round(adx, 2),
        "pdi": round(pdi, 2),
        "mdi": round(mdi, 2),
        "file": POLICY[regime],
    }


def read_current_strategy() -> str | None:
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("STRATEGY_PATH="):
            return line.split("=", 1)[1].strip()
    return None


def set_strategy(filename: str) -> None:
    path = f"/app/strategies/{filename}"
    lines = ENV_FILE.read_text().splitlines()
    out = []
    found = False
    for line in lines:
        if line.startswith("STRATEGY_PATH="):
            out.append(f"STRATEGY_PATH={path}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"STRATEGY_PATH={path}")
    bak = ENV_FILE.with_suffix(ENV_FILE.suffix + f".bak.regime.{int(time.time())}")
    bak.write_text(ENV_FILE.read_text())
    ENV_FILE.write_text("\n".join(out) + "\n")
    ACTIVE.write_text(filename.replace(".json", "") + "\n")


def restart_bot() -> str:
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(ROOT), check=False)
    subprocess.run(["docker", "compose", "restart", "bot"], cwd=str(ROOT), check=True)
    time.sleep(3)
    p = subprocess.run(
        ["docker", "logs", "--tail", "25", "upbit-paper-bot"],
        capture_output=True,
        text=True,
    )
    return (p.stdout or "") + (p.stderr or "")


def main() -> None:
    dry = os.environ.get("DRY_RUN", "0") == "1"
    force = os.environ.get("FORCE", "0") == "1"
    info = classify(fetch_days())
    target = info["file"]
    target_path = f"/app/strategies/{target}"
    current = read_current_strategy()
    local = STRAT_DIR / target
    if not local.exists():
        raise SystemExit(f"missing strategy file: {local}")

    rec = {
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "regime": info["regime"],
        "adx": info["adx"],
        "pdi": info["pdi"],
        "mdi": info["mdi"],
        "old": current,
        "new": target_path,
        "changed": current != target_path,
        "dry_run": dry,
    }

    print(json.dumps({**info, "current_strategy": current}, ensure_ascii=False, indent=2))

    if current == target_path and not force:
        print("already on correct strategy — no-op")
        rec["action"] = "noop"
    elif dry:
        print(f"DRY_RUN would switch {current} -> {target_path}")
        rec["action"] = "dry_run"
    else:
        set_strategy(target)
        logs = restart_bot()
        rec["action"] = "switched"
        print("--- bot logs ---")
        print(logs)
        print(f"switched {current} -> {target_path}")

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
