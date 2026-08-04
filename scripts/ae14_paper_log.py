#!/usr/bin/env python3
"""AE14 — Paper event logger for research shelf rules (no orders).

Frozen rules (see reports/improve/20260729-ae14-paper-log-spec.md):
  H1:      fundingRate <= -0.0002  → paper long next UTC day
  H_rich:  Upbit premium >= 0.004563 → paper fade (short) next UTC day

Reads latest forward snaps (or fetches premium), appends paper-events.jsonl
only when a rule fires. Never touches LIVE / Policy C / STRATEGY_PATH.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("AUTO_TRADE_ROOT", Path(__file__).resolve().parents[1]))
COLLECT = ROOT / "reports" / "ae12-collect"
PAPER_DIR = ROOT / "reports" / "ae14-paper"
EVENTS = PAPER_DIR / "paper-events.jsonl"
PREMIUM_LOG = PAPER_DIR / "upbit-premium.jsonl"

H1_THRESH = -0.0002
RICH_CUT = 0.004563296109377913  # AE13 train 90th — frozen
PRIMARY_RT_BPS = 20


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_json(url: str):
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "ae14-paper-log"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def append_jsonl(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def last_jsonl(path: Path) -> dict | None:
    if not path.exists():
        return None
    last = None
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                last = json.loads(line)
    return last


def fetch_premium() -> dict:
    krw_btc = get_json("https://api.upbit.com/v1/ticker?markets=KRW-BTC")[0]
    usdt_btc = get_json("https://api.upbit.com/v1/ticker?markets=USDT-BTC")[0]
    time.sleep(0.05)
    krw_usdt = get_json("https://api.upbit.com/v1/ticker?markets=KRW-USDT")[0]
    kb = float(krw_btc["trade_price"])
    ub = float(usdt_btc["trade_price"])
    ku = float(krw_usdt["trade_price"])
    prem = kb / (ub * ku) - 1.0
    rec = {
        "ts_utc": utc_now(),
        "krw_btc": kb,
        "usdt_btc": ub,
        "krw_usdt": ku,
        "premium": round(prem, 8),
    }
    append_jsonl(PREMIUM_LOG, rec)
    return rec


def already_logged(rule: str, source: str, signal_date: str) -> bool:
    if not EVENTS.exists():
        return False
    with EVENTS.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            e = json.loads(line)
            if (
                e.get("rule") == rule
                and e.get("source") == source
                and e.get("signal_date") == signal_date
            ):
                return True
    return False


def emit(rule: str, source: str, signal: float, extra: dict | None = None) -> dict | None:
    ts = utc_now()
    signal_date = ts[:10]
    if already_logged(rule, source, signal_date):
        return None
    rec = {
        "ts_utc": ts,
        "signal_date": signal_date,
        "rule": rule,
        "source": source,
        "signal": signal,
        "horizon": "next_utc_day",
        "action": "long" if rule == "H1" else "fade_short",
        "cost_rt_bps_assumed": PRIMARY_RT_BPS,
        "status": "paper",
        "promote": False,
    }
    if extra:
        rec.update(extra)
    append_jsonl(EVENTS, rec)
    return rec


def main() -> int:
    fired = []
    okx = last_jsonl(COLLECT / "okx-funding.jsonl")
    bitget = last_jsonl(COLLECT / "bitget-funding.jsonl")
    if okx and okx.get("fundingRate") is not None and okx["fundingRate"] <= H1_THRESH:
        e = emit("H1", "okx", okx["fundingRate"], {"fundingRate": okx["fundingRate"]})
        if e:
            fired.append(e)
    if (
        bitget
        and bitget.get("fundingRate") is not None
        and bitget["fundingRate"] <= H1_THRESH
    ):
        e = emit(
            "H1",
            "bitget",
            bitget["fundingRate"],
            {"fundingRate": bitget["fundingRate"]},
        )
        if e:
            fired.append(e)

    prem = fetch_premium()
    if prem["premium"] >= RICH_CUT:
        e = emit("H_rich", "upbit", prem["premium"], {"premium": prem["premium"]})
        if e:
            fired.append(e)

    summary = {
        "ts_utc": utc_now(),
        "okx_funding": None if not okx else okx.get("fundingRate"),
        "bitget_funding": None if not bitget else bitget.get("fundingRate"),
        "premium": prem.get("premium"),
        "fired_n": len(fired),
        "fired": fired,
        "events_log": str(EVENTS),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
