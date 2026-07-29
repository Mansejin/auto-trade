#!/usr/bin/env python3
"""Premium watcher — conditionally overlay kimchi-rich strategy on top of Policy C.

Runs on cron (e.g. */30). Checks Upbit KRW premium:
  - If premium >= RICH_CUT → switch to kimchi-rich strategy
  - If premium < RICH_CUT  → restore Policy C regime strategy

Does NOT retune the rich cut. Does NOT auto market-sell.
Respects the same dwell / position-skip guards as regime switch.

Requires: remote_regime_switch.py in the same directory (imports classify, guards).
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("AUTO_TRADE_ROOT", str(Path.home() / "auto-trade")))
STRAT_DIR = ROOT / "strategies"
ENV_FILE = ROOT / ".env"
LOG_FILE = ROOT / "logs" / "premium-watcher.jsonl"
TEXT_LOG = ROOT / "logs" / "premium-watcher.log"
REGIME_CURRENT = ROOT / "logs" / "regime-current.json"

# Frozen from AE13 train 90th — do NOT retune
RICH_CUT = float(os.environ.get("PREMIUM_RICH_CUT", "0.004563"))
KIMCHI_STRATEGY = "kimchi-rich-preposition-skip-v1.json"
# Minimum seconds between overlay switches (separate from regime dwell)
OVERLAY_COOLDOWN_SEC = int(os.environ.get("OVERLAY_COOLDOWN_SEC", "3600"))

# Policy C map — must match remote_regime_switch.py (sideways Williams + dwell gate)
POLICY = {
    "bull": "regime-bull-trend-4h-v2.json",
    "transition": "regime-bull-trend-4h-v2.json",
    "bear": "krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "regime-sideways-mr-1h-williams-v1.json",
}
SIDEWAYS_FALLBACK = "regime-sideways-mr-4h-v5.json"


def log_line(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line)
    try:
        TEXT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with TEXT_LOG.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def append_log(rec: dict) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def get_json(url: str):
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "premium-watcher"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_premium() -> dict:
    """Fetch Upbit KRW-BTC premium vs USDT-BTC * KRW-USDT."""
    kb = float(get_json("https://api.upbit.com/v1/ticker?markets=KRW-BTC")[0]["trade_price"])
    ub = float(get_json("https://api.upbit.com/v1/ticker?markets=USDT-BTC")[0]["trade_price"])
    time.sleep(0.05)
    ku = float(get_json("https://api.upbit.com/v1/ticker?markets=KRW-USDT")[0]["trade_price"])
    prem = kb / (ub * ku) - 1.0
    return {"krw_btc": kb, "usdt_btc": ub, "krw_usdt": ku, "premium": prem}


def read_current_strategy() -> str | None:
    if not ENV_FILE.exists():
        return None
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("STRATEGY_PATH="):
            return line.split("=", 1)[1].strip()
    return None


def current_regime() -> str:
    """Read last regime from regime-current.json (written by regime switch cron)."""
    if REGIME_CURRENT.exists():
        try:
            data = json.loads(REGIME_CURRENT.read_text())
            return data.get("regime", "bear")
        except (json.JSONDecodeError, OSError):
            pass
    return "bear"


def policy_strategy_for_regime(regime: str) -> str:
    # Prefer last selected_file from regime engine (includes dwell>=7 Williams gate).
    if REGIME_CURRENT.exists():
        try:
            data = json.loads(REGIME_CURRENT.read_text())
            sel = data.get("selected_file")
            if sel and (STRAT_DIR / sel).exists():
                return sel
            if (
                data.get("regime") == "sideways"
                and data.get("sideways_gate") == "fallback_v5_dwell"
            ):
                return SIDEWAYS_FALLBACK
        except (json.JSONDecodeError, OSError):
            pass
    return POLICY.get(regime, POLICY["bear"])


def set_strategy(filename: str) -> None:
    """Update .env STRATEGY_PATH and ACTIVE_STRATEGY pointer."""
    import subprocess

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
    bak = ENV_FILE.with_suffix(f".bak.premium.{int(time.time())}")
    bak.write_text(ENV_FILE.read_text())
    ENV_FILE.write_text("\n".join(out) + "\n")
    active = STRAT_DIR / "ACTIVE_STRATEGY"
    active.write_text(filename.replace(".json", "") + "\n")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(ROOT), check=False)
    subprocess.run(["docker", "compose", "restart", "bot"], cwd=str(ROOT), check=False)


def last_overlay_age_sec() -> float | None:
    """Seconds since last premium-watcher switch action."""
    if not LOG_FILE.exists():
        return None
    last_ts = None
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("action") in ("overlay_on", "overlay_off"):
                last_ts = rec.get("ts_epoch")
    if last_ts is None:
        return None
    return time.time() - float(last_ts)


def is_kimchi_active() -> bool:
    cur = read_current_strategy() or ""
    return KIMCHI_STRATEGY.replace(".json", "") in cur


def main() -> None:
    dry = os.environ.get("DRY_RUN", "0") == "1"

    prem_data = fetch_premium()
    premium = prem_data["premium"]
    is_rich = premium >= RICH_CUT
    regime = current_regime()
    policy_file = policy_strategy_for_regime(regime)
    kimchi_on = is_kimchi_active()

    rec = {
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts_epoch": int(time.time()),
        "premium": round(premium, 8),
        "rich_cut": RICH_CUT,
        "is_rich": is_rich,
        "regime": regime,
        "policy_file": policy_file,
        "kimchi_on": kimchi_on,
        "dry_run": dry,
    }

    log_line(f"premium={premium:.6f} rich={is_rich} regime={regime} kimchi_on={kimchi_on}")

    if is_rich and not kimchi_on:
        # Check cooldown
        age = last_overlay_age_sec()
        if age is not None and age < OVERLAY_COOLDOWN_SEC:
            rec["action"] = "cooldown_block"
            rec["cooldown_remaining_sec"] = int(OVERLAY_COOLDOWN_SEC - age)
            log_line(f"action=cooldown_block age={age:.0f}s < {OVERLAY_COOLDOWN_SEC}s")
        elif dry:
            rec["action"] = "dry_overlay_on"
            log_line(f"action=dry_overlay_on would switch to {KIMCHI_STRATEGY}")
        else:
            # Verify kimchi JSON exists
            if not (STRAT_DIR / KIMCHI_STRATEGY).exists():
                rec["action"] = "missing_kimchi_json"
                log_line(f"action=missing_kimchi_json {STRAT_DIR / KIMCHI_STRATEGY}")
            else:
                set_strategy(KIMCHI_STRATEGY)
                rec["action"] = "overlay_on"
                rec["old"] = read_current_strategy()
                rec["new"] = f"/app/strategies/{KIMCHI_STRATEGY}"
                log_line(f"action=overlay_on premium={premium:.6f} -> {KIMCHI_STRATEGY}")

    elif not is_rich and kimchi_on:
        # Premium dropped below cut — restore Policy C strategy
        age = last_overlay_age_sec()
        if age is not None and age < OVERLAY_COOLDOWN_SEC:
            rec["action"] = "cooldown_block"
            rec["cooldown_remaining_sec"] = int(OVERLAY_COOLDOWN_SEC - age)
            log_line(f"action=cooldown_block restore age={age:.0f}s < {OVERLAY_COOLDOWN_SEC}s")
        elif dry:
            rec["action"] = "dry_overlay_off"
            log_line(f"action=dry_overlay_off would restore {policy_file}")
        else:
            set_strategy(policy_file)
            rec["action"] = "overlay_off"
            rec["old"] = f"/app/strategies/{KIMCHI_STRATEGY}"
            rec["new"] = f"/app/strategies/{policy_file}"
            log_line(f"action=overlay_off premium={premium:.6f} -> {policy_file}")

    else:
        rec["action"] = "noop"
        if is_rich and kimchi_on:
            log_line("noop: already on kimchi-rich (premium still rich)")
        else:
            log_line("noop: premium normal, policy strategy active")

    append_log(rec)
    print(json.dumps(rec, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
