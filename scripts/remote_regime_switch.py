#!/usr/bin/env python3
"""Server-side daily regime classifier + STRATEGY_PATH switcher (stdlib only).

Ops guards (Policy C rules unchanged):
  - Classify on last *closed* daily candle only.
  - Min dwell: block strategy switches within MIN_DWELL_HOURS (FORCE bypasses dwell only).
  - Before switch: cancel open KRW-BTC orders; if BTC position remains, skip switch.
  - Never auto market-sell the position.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("AUTO_TRADE_ROOT", str(Path.home() / "auto-trade")))
STRAT_DIR = ROOT / "strategies"
ENV_FILE = ROOT / ".env"
LOG_FILE = ROOT / "logs" / "regime-switch.jsonl"
TEXT_LOG = ROOT / "logs" / "regime-switch.log"
REGIME_CURRENT = ROOT / "logs" / "regime-current.json"
ACTIVE = STRAT_DIR / "ACTIVE_STRATEGY"
STATE_FILE = ROOT / "data" / "state.json"
UPBIT_API = "https://api.upbit.com"
MARKET = "KRW-BTC"
BTC_DUST = float(os.environ.get("BTC_POSITION_DUST", "0.00008"))
MIN_DWELL_HOURS = float(os.environ.get("MIN_DWELL_HOURS", "24"))

# Policy C restored 2026-07-31 after famous vs PC race (PC return >> famous both windows).
POLICY = {
    "bull": "regime-bull-trend-4h-v2.json",
    "transition": "regime-bull-trend-4h-v2.json",
    "bear": "krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "regime-sideways-mr-1h-williams-v1.json",
}
SIDEWAYS_WILLIAMS_MIN_DWELL = int(os.environ.get("SIDEWAYS_WILLIAMS_MIN_DWELL", "7"))
SIDEWAYS_FALLBACK = "regime-sideways-mr-4h-v5.json"


def log_line(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}"
    print(line)
    try:
        TEXT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with TEXT_LOG.open("a") as f:
            f.write(line + "\n")
    except OSError as e:
        print(f"warn: could not append {TEXT_LOG}: {e}")


def load_dotenv(path: Path = ENV_FILE) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def fetch_days(want: int = 260) -> list[dict]:
    rows: list[dict] = []
    to = None
    while len(rows) < want:
        url = "https://api.upbit.com/v1/candles/days?market=KRW-BTC&count=200"
        if to:
            url += f"&to={to}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "regime-switch-server",
            },
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


def closed_daily_candles(candles: list[dict]) -> list[dict]:
    if len(candles) < 2:
        raise RuntimeError("need at least 2 daily candles (forming + closed)")
    return candles[:-1]


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
    closed = closed_daily_candles(candles)
    closes = [c["trade_price"] for c in closed]
    highs = [c["high_price"] for c in closed]
    lows = [c["low_price"] for c in closed]
    i = len(closes) - 1
    s50 = sma(closes, 50, i)
    s200 = sma(closes, 200, i)
    pdi, mdi, adx = adx_last(highs, lows, closes)
    if None in (s50, s200, adx, pdi, mdi):
        raise RuntimeError("insufficient candles")

    # Label every closed bar so we can compute sideways dwell ending at i.
    regimes: list[str] = []
    for j in range(len(closes)):
        sj50 = sma(closes, 50, j)
        sj200 = sma(closes, 200, j)
        if sj50 is None or sj200 is None or j < 28:
            regimes.append("warmup")
            continue
        # Recompute ADX/DI at j cheaply via full series endpoint — use last-only helper
        # by slicing; for dwell we only need adx-based sideways vs not on history.
        # Approximate with same rules using rolling endpoint values from adx_last on prefix.
        ph, pl, pc = highs[: j + 1], lows[: j + 1], closes[: j + 1]
        pj_pdi, pj_mdi, pj_adx = adx_last(ph, pl, pc)
        if None in (pj_adx, pj_pdi, pj_mdi):
            regimes.append("warmup")
            continue
        if pj_adx < 20:
            regimes.append("sideways")
        elif pc[j] > sj200 and sj50 > sj200 and pj_pdi >= pj_mdi:
            regimes.append("bull")
        elif pc[j] < sj200 and sj50 < sj200 and pc[j] < sj50 and pj_mdi > pj_pdi:
            regimes.append("bear")
        else:
            regimes.append("transition")

    regime = regimes[i]
    sideways_dwell = 0
    for r in reversed(regimes[: i + 1]):
        if r == "sideways":
            sideways_dwell += 1
        else:
            break

    if regime == "sideways" and sideways_dwell < SIDEWAYS_WILLIAMS_MIN_DWELL:
        strat_file = SIDEWAYS_FALLBACK
        sideways_gate = "fallback_v5_dwell"
    else:
        strat_file = POLICY[regime]
        sideways_gate = "williams" if regime == "sideways" else "n/a"

    return {
        "date": closed[i]["candle_date_time_utc"][:10],
        "regime": regime,
        "close": closes[i],
        "sma50": s50,
        "sma200": s200,
        "adx": round(adx, 2),
        "pdi": round(pdi, 2),
        "mdi": round(mdi, 2),
        "sideways_dwell": sideways_dwell,
        "sideways_gate": sideways_gate,
        "file": strat_file,
        "bar": "closed",
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
    # NAS/opaque compose: set COMPOSE_FILE, COMPOSE_PROJECT_NAME, BOT_COMPOSE_SERVICE, BOT_CONTAINER.
    compose = ["docker", "compose"]
    project = os.environ.get("COMPOSE_PROJECT_NAME", "").strip()
    compose_file = os.environ.get("COMPOSE_FILE", "").strip()
    service = os.environ.get("BOT_COMPOSE_SERVICE", "bot").strip() or "bot"
    container = os.environ.get("BOT_CONTAINER", "upbit-paper-bot").strip() or "upbit-paper-bot"
    if project:
        compose += ["-p", project]
    if compose_file:
        compose += ["-f", compose_file]
    subprocess.run(compose + ["up", "-d"], cwd=str(ROOT), check=False)
    subprocess.run(compose + ["restart", service], cwd=str(ROOT), check=True)
    time.sleep(3)
    p = subprocess.run(
        ["docker", "logs", "--tail", "25", container],
        capture_output=True,
        text=True,
    )
    return (p.stdout or "") + (p.stderr or "")


def last_successful_switch_age_hours() -> float | None:
    """Age since last action=switched only (ignore noop / skip / dwell_block lines)."""
    if not LOG_FILE.exists():
        return None
    last_switched = ""
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("action") == "switched":
                last_switched = line
    if not last_switched:
        return None
    rec = json.loads(last_switched)
    ts = rec.get("ts_epoch")
    if ts is None and rec.get("ts_utc"):
        try:
            ts = time.mktime(time.strptime(rec["ts_utc"], "%Y-%m-%dT%H:%M:%SZ"))
        except ValueError:
            return None
    if not ts:
        return None
    return (time.time() - float(ts)) / 3600.0


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _upbit_jwt(
    access_key: str, secret_key: str, query: dict[str, Any] | None = None
) -> str:
    payload: dict[str, Any] = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
    }
    if query is not None:
        qs = urllib.parse.urlencode(query)
        payload["query_hash"] = hashlib.sha512(qs.encode()).hexdigest()
        payload["query_hash_alg"] = "SHA512"
    header = {"alg": "HS256", "typ": "JWT"}
    s1 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    s2 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret_key.encode(), f"{s1}.{s2}".encode(), hashlib.sha256).digest()
    return f"{s1}.{s2}.{_b64url(sig)}"


def _upbit_request(
    method: str,
    path: str,
    access_key: str,
    secret_key: str,
    query: dict[str, Any] | None = None,
) -> Any:
    query = query or {}
    token = _upbit_jwt(access_key, secret_key, query if query else None)
    url = UPBIT_API + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "regime-switch-server",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(f"Upbit {method} {path} failed: {e.code} {detail}") from e


def paper_btc_position() -> float:
    if not STATE_FILE.exists():
        return 0.0
    try:
        state = json.loads(STATE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return 0.0
    pos = state.get("position") or state.get("portfolio", {}).get("position") or {}
    if isinstance(pos, dict):
        for key in ("qty", "quantity", "btc", "volume"):
            if key in pos:
                try:
                    return float(pos[key] or 0.0)
                except (TypeError, ValueError):
                    return 0.0
    try:
        return float(state.get("btc_balance") or state.get("position_qty") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def cancel_open_orders(access_key: str, secret_key: str) -> dict[str, Any]:
    """Cancel all open KRW-BTC orders. Does not place sells."""
    orders = _upbit_request(
        "GET",
        "/v1/orders",
        access_key,
        secret_key,
        {"market": MARKET, "state": "wait"},
    )
    if not isinstance(orders, list):
        orders = []
    cancelled = []
    failures = []
    for order in orders:
        oid = order.get("uuid")
        if not oid:
            continue
        try:
            _upbit_request(
                "DELETE",
                "/v1/order",
                access_key,
                secret_key,
                {"uuid": oid},
            )
            cancelled.append(oid)
            time.sleep(0.05)
        except Exception as e:  # noqa: BLE001 — log and continue cancelling others
            failures.append({"uuid": oid, "error": str(e)})
    return {
        "open_before": len(orders),
        "cancelled": len(cancelled),
        "failures": failures,
        "ok": len(failures) == 0,
    }


def live_btc_total(access_key: str, secret_key: str) -> float:
    accounts = _upbit_request("GET", "/v1/accounts", access_key, secret_key)
    if not isinstance(accounts, list):
        return 0.0
    for row in accounts:
        if str(row.get("currency", "")).upper() == "BTC":
            bal = float(row.get("balance") or 0.0)
            locked = float(row.get("locked") or 0.0)
            return bal + locked
    return 0.0


def prepare_switch_guards(env: dict[str, str]) -> dict[str, Any]:
    """Cancel open orders; report whether a BTC position blocks the switch."""
    skip_guard = os.environ.get("SKIP_POSITION_GUARD", "0") == "1"
    paper = env.get("PAPER", "true").lower() in {"1", "true", "yes"}
    result: dict[str, Any] = {
        "paper": paper,
        "cancel": None,
        "btc": 0.0,
        "blocked": False,
        "reason": None,
    }
    if skip_guard:
        result["reason"] = "SKIP_POSITION_GUARD=1"
        log_line("guard: SKIP_POSITION_GUARD=1 — not checking position/orders")
        return result

    if paper:
        btc = paper_btc_position()
        result["btc"] = btc
        result["cancel"] = {
            "ok": True,
            "cancelled": 0,
            "note": "paper_mode_no_upbit_cancel",
        }
        if btc > BTC_DUST:
            result["blocked"] = True
            result["reason"] = f"paper_position_btc={btc}"
            log_line(
                f"guard: FAIL skip switch — paper BTC position {btc} > dust {BTC_DUST}"
            )
        else:
            log_line("guard: OK paper flat (or no state) — switch allowed")
        return result

    access = env.get("UPBIT_ACCESS_KEY", "")
    secret = env.get("UPBIT_SECRET_KEY", "")
    if not access or not secret:
        result["blocked"] = True
        result["reason"] = "missing_upbit_keys"
        log_line(
            "guard: FAIL missing UPBIT_ACCESS_KEY/SECRET_KEY in .env — skip switch"
        )
        return result

    try:
        cancel = cancel_open_orders(access, secret)
        result["cancel"] = cancel
        if cancel["ok"]:
            log_line(
                f"guard: cancel orders OK — open_before={cancel['open_before']} "
                f"cancelled={cancel['cancelled']}"
            )
        else:
            log_line(f"guard: cancel orders PARTIAL/FAIL — {cancel}")
            result["blocked"] = True
            result["reason"] = "cancel_orders_failed"
            return result
    except Exception as e:  # noqa: BLE001
        log_line(f"guard: FAIL cancel orders — {e}")
        result["blocked"] = True
        result["reason"] = f"cancel_orders_error:{e}"
        result["cancel"] = {"ok": False, "error": str(e)}
        return result

    try:
        btc = live_btc_total(access, secret)
        result["btc"] = btc
    except Exception as e:  # noqa: BLE001
        log_line(f"guard: FAIL balance lookup — {e}")
        result["blocked"] = True
        result["reason"] = f"balance_error:{e}"
        return result

    if btc > BTC_DUST:
        result["blocked"] = True
        result["reason"] = f"live_position_btc={btc}"
        log_line(
            f"guard: FAIL skip switch — BTC position {btc} > dust {BTC_DUST} "
            "(no auto market-sell; wait until flat)"
        )
    else:
        log_line(f"guard: OK flat after cancel — btc={btc}")
    return result


def main() -> None:
    dry = os.environ.get("DRY_RUN", "0") == "1"
    force = os.environ.get("FORCE", "0") == "1"
    env = load_dotenv()
    info = classify(fetch_days())
    target = info["file"]
    target_path = f"/app/strategies/{target}"
    current = read_current_strategy()
    local = STRAT_DIR / target
    if not local.exists():
        raise SystemExit(f"missing strategy file: {local}")

    rec: dict[str, Any] = {
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts_epoch": int(time.time()),
        "regime": info["regime"],
        "adx": info["adx"],
        "pdi": info["pdi"],
        "mdi": info["mdi"],
        "bar": info.get("bar"),
        "date": info["date"],
        "old": current,
        "new": target_path,
        "changed": current != target_path,
        "dry_run": dry,
    }

    print(
        json.dumps({**info, "current_strategy": current}, ensure_ascii=False, indent=2)
    )

    if current == target_path and not force:
        print("already on correct strategy — no-op")
        rec["action"] = "noop"
        log_line(f"action=noop regime={info['regime']} strategy={target_path}")
    elif dry:
        print(f"DRY_RUN would switch {current} -> {target_path}")
        rec["action"] = "dry_run"
        log_line(f"action=dry_run {current} -> {target_path}")
    else:
        age_h = last_successful_switch_age_hours()
        if (
            not force
            and current != target_path
            and age_h is not None
            and age_h < MIN_DWELL_HOURS
        ):
            rec["action"] = "dwell_block"
            rec["dwell_age_hours"] = round(age_h, 3)
            log_line(
                f"action=dwell_block age_h={age_h:.2f} < {MIN_DWELL_HOURS} "
                f"(FORCE=1 to bypass dwell only) — keep {current}"
            )
        else:
            guard = prepare_switch_guards(env)
            rec["guard"] = {
                "paper": guard.get("paper"),
                "btc": guard.get("btc"),
                "blocked": guard.get("blocked"),
                "reason": guard.get("reason"),
                "cancel": guard.get("cancel"),
            }
            if guard.get("blocked"):
                rec["action"] = "position_skip"
                log_line(f"action=position_skip reason={guard.get('reason')}")
            else:
                set_strategy(target)
                logs = restart_bot()
                rec["action"] = "switched"
                log_line(f"action=switched {current} -> {target_path}")
                print("--- bot logs ---")
                print(logs)
                print(f"switched {current} -> {target_path}")

    if rec.get("action") == "dwell_block" and rec.get("dwell_age_hours") is not None:
        rec["reason"] = (
            f"dwell {rec['dwell_age_hours']}h < {MIN_DWELL_HOURS}h"
        )

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "updated_at": rec["ts_utc"],
        "date": info["date"],
        "regime": info["regime"],
        "close": info["close"],
        "sma50": info["sma50"],
        "sma200": info["sma200"],
        "adx": info["adx"],
        "pdi": info["pdi"],
        "mdi": info["mdi"],
        "sideways_dwell": info.get("sideways_dwell"),
        "sideways_gate": info.get("sideways_gate"),
        "selected_file": target,
        "strategy_path": target_path,
        "action": rec.get("action"),
        "bar": info.get("bar"),
        "engine": "v2",
        "policy": "C_williams_sideways_dwell7",
    }
    try:
        REGIME_CURRENT.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
        )
    except OSError as e:
        print(f"warn: could not write {REGIME_CURRENT}: {e}")

    try:
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"warn: could not append {LOG_FILE}: {e}")

    notify_regime_action(env, rec)


def _basename(path: str | None) -> str:
    if not path:
        return "—"
    return Path(path).name


def notify_regime_action(env: dict[str, str], rec: dict[str, Any]) -> None:
    """Telegram ping for switched / position_skip / dwell_block only.

    Dedupes skip/dwell to once per key per ~20h so cron does not spam.
    """
    action = str(rec.get("action") or "")
    if action not in ("switched", "position_skip", "dwell_block"):
        return
    token = (env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat = (env.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat:
        return

    guard = rec.get("guard") if isinstance(rec.get("guard"), dict) else {}
    reason = rec.get("reason") or guard.get("reason") or ""
    dedupe_key = "|".join(
        [
            action,
            str(rec.get("old") or ""),
            str(rec.get("new") or ""),
            str(reason),
        ]
    )
    stamp_path = LOG_FILE.parent / "regime-notify-last.json"
    if action in ("position_skip", "dwell_block"):
        try:
            prev = json.loads(stamp_path.read_text(encoding="utf-8")) if stamp_path.exists() else {}
        except Exception:
            prev = {}
        if (
            prev.get("key") == dedupe_key
            and isinstance(prev.get("ts"), (int, float))
            and (time.time() - float(prev["ts"])) < 20 * 3600
        ):
            print("telegram notify skipped (dedupe)")
            return

    labels = {
        "switched": "전환됨",
        "position_skip": "포지션 보류",
        "dwell_block": "드웰 보류",
    }
    lines = [
        "======= 레짐 스위치 =======",
        f"액션    {labels.get(action, action)}",
        f"레짐    {rec.get('regime')} · ADX {rec.get('adx')}",
        f"변경    {_basename(rec.get('old'))} → {_basename(rec.get('new'))}",
    ]
    if reason:
        lines.append(f"사유    {reason}")
    lines.append(f"시각    {rec.get('ts_utc')}")
    body = urllib.parse.urlencode(
        {"chat_id": chat, "text": "\n".join(lines)}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        try:
            stamp_path.write_text(
                json.dumps({"key": dedupe_key, "ts": int(time.time())}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass
    except Exception as e:
        print(f"warn: telegram notify failed: {type(e).__name__}")

if __name__ == "__main__":
    main()