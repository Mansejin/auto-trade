"""One tick of empty-slot fill: pick next untried experiment, run cpp-bt (+ optional FT).

Designed for Cursor Automation every 5m. Dedupes via reports/auto-slot-fill/ledger.json.
Does NOT promote LIVE / edit Policy C.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLOTS = ROOT / "config" / "empty-strategy-slots.json"
LEDGER = ROOT / "reports" / "auto-slot-fill" / "ledger.json"
OUT = ROOT / "reports" / "auto-slot-fill"
CPP = ROOT / "cpp-bt" / "build" / "cpp-bt.exe"
DATA = ROOT / "cpp-bt" / "data"
STRAT_TMP = OUT / "_tick_strat.json"
FT = ROOT / "freqtrade-research"
CFG = FT / "user_data" / "config.bitget-rsi-ichi-check.json"
FT_STRAT = FT / "user_data" / "strategies" / "TrendShortV1.py"

WINDOWS = (("h1", "2025-09-01", "2026-02-04"), ("h2", "2026-02-04", "2026-08-05"))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fingerprint(exp: dict) -> str:
    key = json.dumps(exp, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def ensure_data(symbol: str, tf: str) -> Path:
    ftind = DATA / f"{symbol}-{tf}.ftind"
    if ftind.exists():
        return ftind
    py = FT / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)
    feather = (
        FT
        / "user_data"
        / "data"
        / "bitget"
        / "futures"
        / f"{symbol}-{tf}-futures.feather"
    )
    if not feather.exists():
        raise SystemExit(f"missing candles {feather}; download first")
    subprocess.run(
        [str(py), str(ROOT / "cpp-bt" / "tools" / "export_ftind.py"), "--symbol", symbol, "--timeframe", tf],
        cwd=ROOT,
        check=True,
    )
    return ftind


def ensure_cpp() -> None:
    if CPP.exists():
        return
    build = ROOT / "cpp-bt" / "scripts" / "build.ps1"
    if not build.exists():
        raise SystemExit("cpp-bt.exe missing and no build.ps1")
    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(build)],
        cwd=ROOT,
        check=True,
    )
    if not CPP.exists():
        raise SystemExit("cpp-bt build failed")


def queue_for_slot(slot: dict, tried: set[str]) -> list[dict]:
    """Expand a small, prior-aware search queue (not random)."""
    side = slot.get("side")
    exps: list[dict] = []
    tfs = slot.get("timeframes") or ["5m"]
    fee = float((slot.get("criteria") or {}).get("fee", 0.0006))

    if slot["id"] == "scalp_bear_short":
        # Prefer neighbors of RESEARCH_KEEP swing hit; skip known-dead tight scalp fades.
        modes = ["di_cloud", "di_only", "cloud_break"]
        adxs = [12, 15, 18, 20, 25]
        exits = [
            (-0.030, 0.090),
            (-0.035, 0.105),
            (-0.030, 0.120),
            (-0.040, 0.120),
            (-0.025, 0.075),
            (-0.020, 0.080),
        ]
        for tf, mode, adx, (sl, tp) in product(tfs, modes, adxs, exits):
            exp = {
                "slot": slot["id"],
                "tf": tf,
                "mode": mode,
                "adx_min": adx,
                "rsi_max": 55 if mode != "di_only" else 60,
                "sl": sl,
                "tp": tp,
                "trailing": False,
                "fee": fee,
                "family": "trend_short_neighbor",
            }
            if fingerprint(exp) not in tried:
                exps.append(exp)
        return exps

    if slot["id"] == "scalp_bull_long":
        # cpp-bt is short-first today — mark need_new_hypothesis for agent.
        return []

    # transition / sideways: wait until dependants have candidates, else empty
    return []


def _eligible_status(slot: dict) -> bool:
    return slot.get("status") in ("empty", "cash_stopped", "understudy", "research", None)


def _recent_need_hypothesis(ledger: dict, slot_id: str, n: int = 8) -> bool:
    rows = [t for t in ledger.get("tried", []) if t.get("slot") == slot_id]
    return any(t.get("result") == "need_hypothesis" for t in rows[-n:])


def pick_slot(slots_doc: dict, ledger: dict) -> dict | None:
    """Prefer cpp-bt runnable queues; else rotate toolkit / understudy slots for agent hypothesis."""
    cands = {c.get("slot") for c in ledger.get("candidates", [])}
    ordered = sorted(slots_doc["slots"], key=lambda s: s.get("priority", 99))

    for slot in ordered:
        if not _eligible_status(slot):
            continue
        deps = slot.get("depends_on_any_candidate") or []
        if deps and not any(d in cands for d in deps):
            continue
        tried = {t["fingerprint"] for t in ledger.get("tried", []) if t.get("slot") == slot["id"]}
        if queue_for_slot(slot, tried):
            return slot

    for slot in ordered:
        if not _eligible_status(slot):
            continue
        deps = slot.get("depends_on_any_candidate") or []
        if deps and not any(d in cands for d in deps):
            continue
        eng = slot.get("engine") or ""
        if eng == "cpp-bt" and slot["id"] != "scalp_bull_long":
            continue
        if _recent_need_hypothesis(ledger, slot["id"]):
            continue
        return slot
    return None


def write_strat(exp: dict) -> None:
    obj = {
        "name": f"auto-{exp['slot']}",
        "side": "short",
        "symbols": ["BTC_USDT_USDT"],
        "timeframe": exp["tf"],
        "fee": exp["fee"],
        "startup": 80,
        "entry": {
            "mode": exp["mode"],
            "rsi_period": 14,
            "adx_period": 14,
            "adx_min": exp["adx_min"],
            "rsi_max": exp["rsi_max"],
        },
        "exit": {
            "stoploss": exp["sl"],
            "take_profit": exp["tp"],
            "trailing": bool(exp.get("trailing")),
            "trail_pos": 0.0,
            "trail_offset": 0.0,
        },
    }
    save_json(STRAT_TMP, obj)


def cpp_window(exp: dict, start: str, end: str) -> dict:
    write_strat(exp)
    p = subprocess.run(
        [
            str(CPP),
            "run",
            "--strategy",
            str(STRAT_TMP),
            "--data",
            str(DATA),
            "--start",
            start,
            "--end",
            end,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = (p.stdout or "") + (p.stderr or "")
    m = re.search(r"trades=(\d+) pf=([0-9.]+) pnl_pct_sum=([+-]?[0-9.]+)", text)
    if not m:
        return {"trades": 0, "profit_factor": None, "profit_pct": None, "raw": text[-200:]}
    return {
        "trades": int(m.group(1)),
        "profit_factor": float(m.group(2)),
        "profit_pct": float(m.group(3)),
    }


def ft_window(start: str, end: str, exp: dict) -> dict:
    """Fixed-stake FT confirm for short TrendShortV1-shaped params."""
    cfg = load_json(CFG)
    orig_cfg = json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"
    orig_strat = FT_STRAT.read_text(encoding="utf-8")
    try:
        cfg["fee"] = exp["fee"]
        cfg["stake_amount"] = 100
        cfg["dry_run_wallet"] = 1000
        cfg["entry_pricing"]["use_order_book"] = False
        cfg["exit_pricing"]["use_order_book"] = False
        cfg["export"] = "none"
        save_json(CFG, cfg)

        t = orig_strat
        t = re.sub(r"stoploss = -0\.\d+", f"stoploss = {exp['sl']}", t, count=1)
        t = re.sub(
            r'minimal_roi = \{"0": 0\.\d+\}',
            f'minimal_roi = {{"0": {exp["tp"]}}}',
            t,
            count=1,
        )
        t = re.sub(r'entry_mode = "[^"]+"', f'entry_mode = "{exp["mode"]}"', t, count=1)
        t = re.sub(r"adx_min = \d+", f"adx_min = {int(exp['adx_min'])}", t, count=1)
        t = re.sub(r"rsi_max = \d+", f"rsi_max = {int(exp['rsi_max'])}", t, count=1)
        FT_STRAT.write_text(t, encoding="utf-8")

        tr_ft = start.replace("-", "") + "-" + end.replace("-", "")
        p = subprocess.run(
            [
                str(FT / ".venv" / "Scripts" / "freqtrade.exe"),
                "backtesting",
                "--config",
                str(CFG),
                "--strategy",
                "TrendShortV1",
                "--timerange",
                tr_ft,
                "--cache",
                "none",
                "--export",
                "none",
            ],
            cwd=FT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        text = ((p.stdout or "") + "\n" + (p.stderr or "")).replace("│", "|")
        out: dict = {"trades": 0, "profit_factor": None}
        m = re.search(r"Total/Daily Avg Trades\s*\|\s*(\d+)", text)
        if m:
            out["trades"] = int(m.group(1))
        m = re.search(r"Profit factor\s*\|\s*([0-9.]+|nan)", text)
        if m and m.group(1) != "nan":
            out["profit_factor"] = float(m.group(1))
        return out
    finally:
        CFG.write_text(orig_cfg, encoding="utf-8")
        FT_STRAT.write_text(orig_strat, encoding="utf-8")


def passes(crit: dict, h1: dict, h2: dict) -> bool:
    nmin = int(crit.get("min_trades", 20))
    pfmin = float(crit.get("min_pf", 1.2))
    for w in (h1, h2):
        if (w.get("trades") or 0) < nmin:
            return False
        if (w.get("profit_factor") or 0) < pfmin:
            return False
    if crit.get("require_positive_return"):
        for w in (h1, h2):
            if (w.get("profit_pct") or 0) <= 0:
                return False
    return True


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    slots_doc = load_json(SLOTS)
    ledger = load_json(LEDGER) if LEDGER.exists() else {"tried": [], "candidates": [], "banned_families": []}

    slot = pick_slot(slots_doc, ledger)
    if not slot:
        result = {"ok": True, "action": "idle", "reason": "no empty slot with pending queue", "at": utc_now()}
        print(json.dumps(result, indent=2))
        ledger["last_tick"] = result
        save_json(LEDGER, ledger)
        return

    tried_fps = {t["fingerprint"] for t in ledger.get("tried", [])}
    queue = queue_for_slot(slot, tried_fps)

    if not queue:
        row = {
            "fingerprint": fingerprint({"slot": slot["id"], "need": "hypothesis", "at": utc_now()}),
            "slot": slot["id"],
            "result": "need_hypothesis",
            "at": utc_now(),
            "hint": slot.get("hints", []),
        }
        ledger.setdefault("tried", []).append(row)
        ledger["last_tick"] = {
            "ok": True,
            "action": "need_hypothesis",
            "slot": slot["id"],
            "horizon": slot.get("horizon"),
            "engine": slot.get("engine"),
            "live_baseline": slot.get("live_baseline"),
            "message": (
                "No cpp-bt queue left (or toolkit slot). Invent ONE new family from slot hints/seeds; "
                "for CORE understudies must beat live_baseline on both OOS halves; "
                "log fingerprint in ledger; never auto-replace Policy C LIVE."
            ),
            "at": utc_now(),
        }
        save_json(LEDGER, ledger)
        print(json.dumps(ledger["last_tick"], indent=2))
        return

    exp = queue[0]
    fp = fingerprint(exp)
    ensure_cpp()
    ensure_data(slot.get("symbol", "BTC_USDT_USDT"), exp["tf"])

    print(f"tick slot={slot['id']} fp={fp} exp={exp}", flush=True)
    h1 = cpp_window(exp, WINDOWS[0][1], WINDOWS[0][2])
    h2 = cpp_window(exp, WINDOWS[1][1], WINDOWS[1][2])
    crit = slot.get("criteria") or {}
    cpp_pass = passes(crit, h1, h2)

    row = {
        "fingerprint": fp,
        "slot": slot["id"],
        "exp": exp,
        "cpp": {"h1": h1, "h2": h2, "pass": cpp_pass},
        "at": utc_now(),
        "result": "cpp_miss",
    }

    ft = None
    if cpp_pass and slot.get("side") in ("short", "either"):
        ft = {
            "h1": ft_window(WINDOWS[0][1], WINDOWS[0][2], exp),
            "h2": ft_window(WINDOWS[1][1], WINDOWS[1][2], exp),
        }
        ft_pass = passes(crit, ft["h1"], ft["h2"])
        row["ft"] = {**ft, "pass": ft_pass}
        row["result"] = "candidate" if ft_pass else "ft_miss"
        if ft_pass:
            cand = {
                "slot": slot["id"],
                "fingerprint": fp,
                "exp": exp,
                "cpp": row["cpp"],
                "ft": row["ft"],
                "status": "HUMAN_APPROVE",
                "at": utc_now(),
            }
            ledger.setdefault("candidates", []).append(cand)
            save_json(OUT / "candidates" / f"{slot['id']}-{fp}.json", cand)
    elif cpp_pass:
        row["result"] = "cpp_pass_needs_long_engine"
    else:
        row["result"] = "cpp_miss"

    ledger.setdefault("tried", []).append(row)
    ledger["last_tick"] = {
        "ok": True,
        "action": "ran",
        "slot": slot["id"],
        "fingerprint": fp,
        "result": row["result"],
        "cpp_min_pf": min(h1.get("profit_factor") or 0, h2.get("profit_factor") or 0),
        "at": utc_now(),
    }
    # cap tried growth
    if len(ledger["tried"]) > 5000:
        ledger["tried"] = ledger["tried"][-4000:]
    save_json(LEDGER, ledger)
    print(json.dumps(ledger["last_tick"], indent=2))
    if row["result"] == "candidate":
        print("*** CANDIDATE — human approve required before LIVE", flush=True)


if __name__ == "__main__":
    main()
