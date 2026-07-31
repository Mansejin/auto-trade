from __future__ import annotations

import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from equity_curve import equity_curve_from_trades, equity_summary

LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
STATE_PATH = Path(os.getenv("STATE_PATH", "/app/data/state.json"))
RISK_PATH = Path(os.getenv("RISK_PATH", "/app/data/risk.json"))
REGIME_PATH = Path(os.getenv("REGIME_PATH", str(LOG_DIR / "regime-current.json")))
BITGET_STATE_PATH = Path(os.getenv("BITGET_STATE_PATH", "/app/data/bitget_state.json"))
BITGET_LOG_DIR = Path(os.getenv("BITGET_LOG_DIR", "/app/logs/bitget"))
EQUITY_PATH = Path(os.getenv("EQUITY_PATH", str(LOG_DIR / "equity-history.jsonl")))
EQUITY_SAMPLE_SEC = int(os.getenv("EQUITY_SAMPLE_SEC", "300"))
# Host compose usually mounts repo config → /app/config; local fallback = repo config/
_CFG = Path(os.getenv("CONFIG_DIR", "/app/config"))
if not _CFG.is_dir():
    _CFG = Path(__file__).resolve().parent.parent / "config"
SLEEVES_PATH = Path(os.getenv("SLEEVES_PATH", str(_CFG / "sleeves.json")))
SCALP_MAP_PATH = Path(os.getenv("SCALP_MAP_PATH", str(_CFG / "scalp-live-map.json")))
TOKEN = os.getenv("DASHBOARD_TOKEN", "").strip()
BASE_PATH = os.getenv("BASE_PATH", "").strip().rstrip("/")
COOKIE_NAME = "desk_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 14

REGIME_KO = {
    "bull": "상승",
    "bear": "하락",
    "sideways": "횡보",
    "transition": "전환",
}

SWITCH_ACTION_KO = {
    "switched": "전환됨",
    "position_skip": "포지션 보류",
    "dwell_block": "드웰 보류",
    "noop": "유지",
    "dry_run": "드라이런",
}

SCALP_STATUS_KO = {
    "stopped_cash": "중지 · cash",
    "cash_stopped": "중지 · cash",
    "empty_slot_cash": "빈 슬롯 · cash",
    "live": "가동",
    "live_policy_c": "Policy C",
}

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Auto-Trade Desk", docs_url=None, redoc_url=None)

_candle_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_CANDLE_TTL = 45.0


def _p(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{BASE_PATH}{path}" if BASE_PATH else path


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _authorized(token: str | None) -> bool:
    if not TOKEN or not token:
        return False
    if len(token) != len(TOKEN):
        return False
    return secrets.compare_digest(token, TOKEN)


def _set_auth_cookie(resp: Response, value: str, *, secure: bool | None = None) -> None:
    if secure is None:
        secure = bool(BASE_PATH)
    resp.set_cookie(
        COOKIE_NAME,
        value,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path=BASE_PATH or "/",
        secure=secure,
    )


def _clear_auth_cookie(resp: Response) -> None:
    resp.delete_cookie(COOKIE_NAME, path=BASE_PATH or "/")


def require_auth(
    request: Request,
    desk_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> None:
    header = request.headers.get("Authorization", "")
    bearer = header[7:].strip() if header.lower().startswith("bearer ") else ""
    q = request.query_params.get("token")
    if not (_authorized(desk_token) or _authorized(bearer) or _authorized(q)):
        raise HTTPException(status_code=401, detail="unauthorized")


def _tf_to_tv(tf: str) -> str:
    t = tf.strip().lower()
    mapping = {
        "1m": "1",
        "3m": "3",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "60m": "60",
        "1h": "60",
        "4h": "240",
        "1d": "D",
        "d": "D",
    }
    return mapping.get(t, "60")


def _tf_to_upbit(tf: str) -> tuple[str, int | None, int]:
    """Return (kind, minute_unit, period_seconds)."""
    t = tf.strip().lower()
    minute_map = {
        "1m": (1, 60),
        "3m": (3, 180),
        "5m": (5, 300),
        "10m": (10, 600),
        "15m": (15, 900),
        "30m": (30, 1800),
        "60m": (60, 3600),
        "1h": (60, 3600),
        "240m": (240, 14400),
        "4h": (240, 14400),
    }
    if t in ("1d", "d", "day", "days"):
        return ("days", None, 86400)
    if t in minute_map:
        unit, sec = minute_map[t]
        return ("minutes", unit, sec)
    return ("minutes", 60, 3600)


def _parse_iso_ts(raw: str) -> int | None:
    s = (raw or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        if "T" in s and len(s) == 19:
            s = s + "+00:00"
        dt = datetime.fromisoformat(s)
        return int(dt.timestamp())
    except Exception:
        return None


def _fetch_upbit_candles(market: str, timeframe: str, count: int = 200) -> list[dict[str, Any]]:
    kind, unit, _period = _tf_to_upbit(timeframe)
    count = max(1, min(int(count), 200))
    cache_key = f"{market}|{kind}|{unit}|{count}"
    now = time.time()
    hit = _candle_cache.get(cache_key)
    if hit and now - hit[0] < _CANDLE_TTL:
        return hit[1]

    if kind == "days":
        url = f"https://api.upbit.com/v1/candles/days?market={urllib.parse.quote(market)}&count={count}"
    else:
        url = (
            f"https://api.upbit.com/v1/candles/minutes/{unit}"
            f"?market={urllib.parse.quote(market)}&count={count}"
        )
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": "auto-trade-desk"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"upbit candles http {e.code}") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upbit candles failed: {e}") from e

    if not isinstance(raw, list):
        raise HTTPException(status_code=502, detail="upbit candles bad payload")

    out: list[dict[str, Any]] = []
    for c in reversed(raw):
        ts = _parse_iso_ts(str(c.get("candle_date_time_utc") or ""))
        if ts is None:
            continue
        out.append(
            {
                "time": ts,
                "open": float(c["opening_price"]),
                "high": float(c["high_price"]),
                "low": float(c["low_price"]),
                "close": float(c["trade_price"]),
            }
        )
    _candle_cache[cache_key] = (now, out)
    return out


def _trade_markers(
    trades: list[dict[str, Any]],
    candle_times: list[int],
    period_seconds: int,
) -> list[dict[str, Any]]:
    if not trades or not candle_times:
        return []
    times_set = set(candle_times)
    markers: list[dict[str, Any]] = []
    for t in trades:
        side = str(t.get("side") or "").lower()
        if side not in ("buy", "sell"):
            continue
        ts = _parse_iso_ts(str(t.get("ts") or ""))
        if ts is None:
            continue
        bucket = ts - (ts % period_seconds)
        chosen = None
        for ct in candle_times:
            if ct <= ts:
                chosen = ct
            else:
                break
        if chosen is None:
            continue
        if bucket in times_set and bucket <= ts:
            chosen = bucket
        if side == "buy":
            markers.append(
                {
                    "time": chosen,
                    "position": "belowBar",
                    "color": "#ef5350",
                    "shape": "arrowUp",
                    "text": "매수",
                }
            )
        else:
            markers.append(
                {
                    "time": chosen,
                    "position": "aboveBar",
                    "color": "#2962ff",
                    "shape": "arrowDown",
                    "text": "매도",
                }
            )
    markers.sort(key=lambda m: (m["time"], 0 if m["text"] == "매수" else 1))
    return markers


def healthz() -> dict[str, str]:
    return {"ok": "1", "base_path": BASE_PATH or "/"}


def index(
    request: Request,
    desk_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Response:
    if _authorized(desk_token) or _authorized(request.query_params.get("token")):
        if request.query_params.get("token") and not desk_token:
            resp = RedirectResponse(_p("/"), status_code=302)
            xf = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
            secure = request.url.scheme == "https" or xf == "https"
            _set_auth_cookie(resp, request.query_params.get("token") or "", secure=secure)
            return resp
        return FileResponse(STATIC / "index.html")
    return FileResponse(STATIC / "login.html")


def equity_page(
    request: Request,
    desk_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Response:
    if _authorized(desk_token) or _authorized(request.query_params.get("token")):
        if request.query_params.get("token") and not desk_token:
            resp = RedirectResponse(_p("/equity"), status_code=302)
            xf = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
            secure = request.url.scheme == "https" or xf == "https"
            _set_auth_cookie(resp, request.query_params.get("token") or "", secure=secure)
            return resp
        return FileResponse(STATIC / "equity.html")
    return FileResponse(STATIC / "login.html")

def login(request: Request, token: str = Form(...)) -> Response:
    if not _authorized(token.strip()):
        return RedirectResponse(_p("/?e=1"), status_code=303)
    resp = RedirectResponse(_p("/"), status_code=303)
    xf = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    secure = request.url.scheme == "https" or xf == "https"
    resp.set_cookie(
        COOKIE_NAME,
        token.strip(),
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path=BASE_PATH or "/",
        secure=secure,
    )
    return resp


def logout() -> Response:
    resp = RedirectResponse(_p("/"), status_code=303)
    _clear_auth_cookie(resp)
    return resp


def _last_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        last = ""
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip():
                    last = line
        return json.loads(last) if last else {}
    except Exception:
        return {}


def _load_regime() -> dict[str, Any]:
    """Prefer logs/regime-current.json; fall back to last regime-switch.jsonl line."""
    regime = _load_json(REGIME_PATH)
    if regime.get("regime"):
        return regime
    row = _last_jsonl(LOG_DIR / "regime-switch.jsonl")
    if not row:
        return {}
    return {
        "updated_at": row.get("ts_utc"),
        "regime": row.get("regime"),
        "adx": row.get("adx"),
        "pdi": row.get("pdi"),
        "mdi": row.get("mdi"),
        "selected_file": Path(str(row.get("new") or "")).name or None,
        "action": row.get("action"),
        "reason": row.get("reason"),
        "engine": "v2",
        "policy": "C",
        "source": "regime-switch.jsonl",
    }


def _load_switch() -> dict[str, Any] | None:
    row = _last_jsonl(LOG_DIR / "regime-switch.jsonl")
    if not row:
        return None
    action = str(row.get("action") or "") or None
    guard = row.get("guard") if isinstance(row.get("guard"), dict) else {}
    reason = row.get("reason") or guard.get("reason")
    if not reason and action == "dwell_block":
        age = row.get("dwell_age_hours")
        reason = f"dwell {age}h < min" if age is not None else "dwell min not met"
    return {
        "action": action,
        "action_label": SWITCH_ACTION_KO.get(action or "", action),
        "ts": row.get("ts_utc") or row.get("ts"),
        "regime": row.get("regime"),
        "from": Path(str(row.get("old") or row.get("from") or "")).name or None,
        "to": Path(str(row.get("new") or row.get("to") or "")).name or None,
        "reason": reason,
        "dwell_age_hours": row.get("dwell_age_hours"),
    }


def _load_transfer_pending() -> dict[str, Any] | None:
    """Optional pending transfer approve request beside state.json."""
    path = Path(os.getenv("TRANSFER_PENDING_PATH", str(STATE_PATH.parent / "transfer_pending.json")))
    raw = _load_json(path)
    if not raw or str(raw.get("status") or "pending") != "pending":
        return None
    return {
        "code": raw.get("code"),
        "direction": raw.get("direction"),
        "coin": raw.get("coin"),
        "amount": raw.get("amount"),
        "created_at": raw.get("created_at") or raw.get("ts") or raw.get("requested_at"),
        "detail": raw.get("detail"),
        "expires_at": raw.get("expires_at"),
    }


def _load_switch_history(limit: int = 20) -> list[dict[str, Any]]:
    """Interesting switch events newest-first. Skips routine noop unless file changed."""
    path = LOG_DIR / "regime-switch.jsonl"
    if not path.exists():
        return []
    interesting = {"switched", "position_skip", "dwell_block"}
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                action = str(row.get("action") or "")
                changed = bool(row.get("changed"))
                if action not in interesting and not changed:
                    continue
                guard = row.get("guard") if isinstance(row.get("guard"), dict) else {}
                reason = row.get("reason") or guard.get("reason")
                if not reason and action == "dwell_block":
                    age = row.get("dwell_age_hours")
                    reason = f"dwell {age}h < min" if age is not None else "dwell min not met"
                rows.append(
                    {
                        "ts": row.get("ts_utc") or row.get("ts"),
                        "action": action,
                        "action_label": SWITCH_ACTION_KO.get(action, action or "—"),
                        "regime": row.get("regime"),
                        "regime_label": REGIME_KO.get(
                            str(row.get("regime") or "").lower(), row.get("regime")
                        ),
                        "adx": row.get("adx"),
                        "from": Path(str(row.get("old") or row.get("from") or "")).name or None,
                        "to": Path(str(row.get("new") or row.get("to") or "")).name or None,
                        "changed": changed,
                        "dry_run": bool(row.get("dry_run")),
                        "reason": reason,
                    }
                )
    except Exception:
        return []
    rows.reverse()
    return rows[: max(1, min(int(limit), 100))]


def _basename(path_or_name: Any) -> str | None:
    if not path_or_name:
        return None
    return Path(str(path_or_name)).name or None


def _load_sleeves(regime_code: str | None) -> dict[str, Any]:
    sleeves = _load_json(SLEEVES_PATH)
    scalp_map = _load_json(SCALP_MAP_PATH)
    weights = sleeves.get("weights") or {}
    venues = sleeves.get("venues") or {}
    regimes = sleeves.get("regimes") or {}
    slot = regimes.get(regime_code or "") or {}
    core_slot = slot.get("core") or {}
    scalp_slot = slot.get("scalp") or {}
    scalp_status = (
        scalp_map.get("status")
        or scalp_slot.get("status")
        or "stopped_cash"
    )
    core_status = core_slot.get("status") or "live_policy_c"
    return {
        "ratio": weights.get("ratio") or "5:5",
        "core_pct": weights.get("core_pct"),
        "scalp_pct": weights.get("scalp_pct"),
        "seed_policy": sleeves.get("seed_policy") or {},
        "core": {
            "label": (venues.get("core") or {}).get("label") or "장타",
            "venue": (venues.get("core") or {}).get("venue") or "upbit_spot",
            "bot": (venues.get("core") or {}).get("bot") or "upbit-paper-bot",
            "status": core_status,
            "status_label": SCALP_STATUS_KO.get(core_status, core_status),
            "strategy": _basename(core_slot.get("strategy")),
            "notes": core_slot.get("notes"),
        },
        "scalp": {
            "label": (venues.get("scalp") or {}).get("label") or "단타",
            "venue": (venues.get("scalp") or {}).get("venue") or "bitget_uta_futures",
            "bot": scalp_map.get("bot")
            or (venues.get("scalp") or {}).get("bot")
            or "bitget-futures-bot",
            "status": scalp_status,
            "status_label": SCALP_STATUS_KO.get(scalp_status, scalp_status),
            "strategy": _basename(scalp_slot.get("strategy") or (scalp_map.get("map") or {}).get(regime_code or "")),
            "notes": scalp_slot.get("notes")
            or ((scalp_map.get("switch_notes") or [None])[-1] if scalp_map else None),
        },
        "source": str(SLEEVES_PATH.name) if SLEEVES_PATH.exists() else None,
    }


def _mark_upbit_equity(status: dict[str, Any], state: dict[str, Any]) -> float | None:
    price = status.get("price")
    if price is None:
        return None
    cash = status.get("krw")
    if cash is None:
        cash = status.get("cash")
    if cash is None:
        cash = state.get("cash")
    if cash is None:
        return None
    pos = status.get("position") or state.get("position") or {}
    qty = float(pos.get("qty") or 0) if isinstance(pos, dict) else 0.0
    return float(cash) + qty * float(price)


def _maybe_sample_equity(status: dict[str, Any], state: dict[str, Any]) -> None:
    eq = _mark_upbit_equity(status, state)
    if eq is None:
        return
    now = time.time()
    # Prefer LOG_DIR; fall back to /tmp if logs are mounted read-only (desk compose).
    paths = [EQUITY_PATH, Path("/tmp/equity-history.jsonl")]
    last: dict[str, Any] = {}
    active = EQUITY_PATH
    for path in paths:
        hit = _last_jsonl(path)
        if hit:
            last = hit
            active = path
            break
    if last:
        ts = _parse_iso_ts(str(last.get("ts") or ""))
        if ts is not None and (now - ts) < EQUITY_SAMPLE_SEC:
            return
        try:
            if abs(float(last.get("equity")) - eq) < 1 and ts is not None and (now - ts) < EQUITY_SAMPLE_SEC * 2:
                return
        except Exception:
            pass
    pos = status.get("position") or state.get("position") or {}
    bg = _load_bitget()
    point = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "equity": round(eq, 2),
        "cash": status.get("krw") if status.get("krw") is not None else state.get("cash"),
        "price": status.get("price"),
        "qty": float(pos.get("qty") or 0) if isinstance(pos, dict) else 0.0,
        "bitget_usdt": bg.get("cash"),
        "source": "sample",
    }
    payload = json.dumps(point, ensure_ascii=False) + "\n"
    for path in paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(payload)
            return
        except Exception:
            continue


def _read_equity_history() -> list[dict[str, Any]]:
    for path in (EQUITY_PATH, Path("/tmp/equity-history.jsonl")):
        if not path.exists():
            continue
        out: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except Exception:
                        continue
                    if row.get("equity") is None:
                        continue
                    out.append(row)
        except Exception:
            continue
        if out:
            return out
    return []

def _load_bitget() -> dict[str, Any]:
    bitget_state = _load_json(BITGET_STATE_PATH)
    bitget_status = _load_json(BITGET_LOG_DIR / "status.json")
    text_path = BITGET_LOG_DIR / "latest_status.txt"
    latest_text = ""
    if text_path.exists():
        latest_text = text_path.read_text(encoding="utf-8", errors="ignore")[:8000]
    if not bitget_state and not bitget_status:
        return {
            "running": False,
            "latest_text": latest_text,
            "recent_trades": [],
        }
    bs = bitget_status or {}
    trades = bitget_state.get("trades") or []
    cash = bs.get("cash")
    if cash is None:
        cash = bs.get("usdt")
    if cash is None:
        cash = bitget_state.get("cash")
    return {
        "running": True,
        "exchange": "bitget",
        "mode": bs.get("mode") or bitget_state.get("mode"),
        "strategy": bs.get("strategy") or bitget_state.get("strategy"),
        "market": bs.get("market") or bitget_state.get("market"),
        "signal": bs.get("signal"),
        "cash": cash,
        "position": bs.get("position") or bitget_state.get("position"),
        "latest_text": latest_text,
        "recent_trades": trades[-8:] if isinstance(trades, list) else [],
    }


def api_status(_: None = Depends(require_auth)) -> dict[str, Any]:
    status_path = LOG_DIR / "status.json"
    status = _load_json(status_path)
    state = _load_json(STATE_PATH)
    risk = _load_json(RISK_PATH)
    regime_raw = _load_regime()
    text_path = LOG_DIR / "latest_status.txt"
    latest_text = ""
    stale = True
    mtime = None
    for p in (status_path, text_path):
        if p.exists():
            mt = p.stat().st_mtime
            mtime = mt if mtime is None else max(mtime, mt)
    if mtime is not None:
        stale = (time.time() - mtime) > 900
    if text_path.exists():
        latest_text = text_path.read_text(encoding="utf-8", errors="ignore")

    if not status:
        status = {
            "mode": state.get("mode"),
            "strategy": state.get("strategy"),
            "market": state.get("market"),
            "krw": state.get("cash"),
            "position": state.get("position"),
            "signal": "unknown",
        }
    if risk:
        status["risk"] = {**(status.get("risk") or {}), **risk}

    _maybe_sample_equity(status, state)

    trades = state.get("trades") or []
    recent = trades[-8:] if isinstance(trades, list) else []

    market = str(status.get("market") or state.get("market") or "KRW-BTC")
    tv_symbol = "UPBIT:BTCKRW"
    if market.startswith("KRW-"):
        base = market.split("-", 1)[1]
        tv_symbol = f"UPBIT:{base}KRW"

    regime_code = str(regime_raw.get("regime") or "").lower() or None
    switch = _load_switch()
    regime = None
    if regime_code:
        action = regime_raw.get("action") or (switch or {}).get("action")
        regime = {
            "code": regime_code,
            "label": REGIME_KO.get(regime_code, regime_code),
            "date": regime_raw.get("date"),
            "updated_at": regime_raw.get("updated_at"),
            "adx": regime_raw.get("adx"),
            "pdi": regime_raw.get("pdi"),
            "mdi": regime_raw.get("mdi"),
            "selected_file": _basename(regime_raw.get("selected_file"))
            or _basename(regime_raw.get("strategy_path")),
            "engine": regime_raw.get("engine") or "v2",
            "policy": regime_raw.get("policy") or "C",
            "action": action,
            "action_label": SWITCH_ACTION_KO.get(str(action or ""), action),
        }

    return {
        "ok": True,
        "stale": stale,
        "mtime": mtime,
        "base_path": BASE_PATH or "",
        "status": status,
        "regime": regime,
        "switch": switch,
        "switch_history": _load_switch_history(20),
        "transfer": _load_transfer_pending(),
        "sleeves": _load_sleeves(regime_code),
        "bitget": _load_bitget(),
        "recent_trades": recent,
        "latest_text": latest_text,
        "tv_symbol": tv_symbol,
        "tv_interval": _tf_to_tv(str(status.get("timeframe") or "60")),
        "market": market,
        "timeframe": str(status.get("timeframe") or "1h"),
    }


def api_equity(
    _: None = Depends(require_auth),
    range: str = "30d",
    bh: int = 1,
) -> dict[str, Any]:
    status = _load_json(LOG_DIR / "status.json")
    state = _load_json(STATE_PATH)
    if not status:
        status = {
            "krw": state.get("cash"),
            "cash": state.get("cash"),
            "position": state.get("position"),
            "market": state.get("market"),
            "price": None,
        }
    _maybe_sample_equity(status, state)

    history = _read_equity_history()
    market = str(status.get("market") or state.get("market") or "KRW-BTC")
    source = "history"
    range_key = (range or "30d").strip().lower()
    if range_key not in ("7d", "30d", "90d", "180d", "all"):
        range_key = "30d"

    if len(history) < 2:
        trades = state.get("trades") or []
        if not isinstance(trades, list):
            trades = []
        end_cash = status.get("krw")
        if end_cash is None:
            end_cash = status.get("cash")
        if end_cash is None:
            end_cash = state.get("cash") or 0
        pos = status.get("position") or state.get("position") or {}
        end_qty = float(pos.get("qty") or 0) if isinstance(pos, dict) else 0.0
        try:
            candles = _fetch_upbit_candles(market, "1d", count=200)
            daily = [(int(c["time"]), float(c["close"])) for c in candles]
            rebuilt = equity_curve_from_trades(
                trades, daily, float(end_cash), end_qty, parse_iso_ts=_parse_iso_ts
            )
            if rebuilt:
                history = rebuilt
                source = "trades_mtm"
                tip = _mark_upbit_equity(status, state)
                if tip is not None:
                    history.append(
                        {
                            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "equity": round(tip, 2),
                            "price": status.get("price"),
                            "source": "live",
                        }
                    )
        except Exception as e:
            return {
                "ok": False,
                "error": f"equity rebuild failed: {e}",
                "points": history,
                "summary": equity_summary(history),
                "source": source,
                "range": range_key,
                "market": market,
            }

    range_days = {"7d": 7, "30d": 30, "90d": 90, "180d": 180, "all": None}[range_key]
    if range_days is not None and history:
        cutoff = time.time() - range_days * 86400
        filtered: list[dict[str, Any]] = []
        for p in history:
            raw_ts = str(p.get("ts") or "")
            ts = _parse_iso_ts(raw_ts)
            if ts is None and len(raw_ts) == 10:
                ts = _parse_iso_ts(raw_ts + "T00:00:00+00:00")
            if ts is None or ts >= cutoff:
                filtered.append(p)
        history = filtered or history[-1:]

    bh_on = bool(int(bh))
    if bh_on and len(history) >= 2:
        price_by_day: dict[str, float] = {}
        for p in history:
            if p.get("price") is not None:
                day = str(p.get("ts") or "")[:10]
                if len(day) == 10:
                    price_by_day[day] = float(p["price"])
        try:
            candles = _fetch_upbit_candles(market, "1d", count=200)
            for c in candles:
                day = datetime.fromtimestamp(int(c["time"]), tz=timezone.utc).strftime("%Y-%m-%d")
                price_by_day.setdefault(day, float(c["close"]))
        except Exception:
            pass

        start_eq = float(history[0]["equity"])
        start_day = str(history[0].get("ts") or "")[:10]
        start_px = price_by_day.get(start_day)
        if start_px is None:
            for day in sorted(price_by_day):
                if day >= start_day:
                    start_px = price_by_day[day]
                    break
        if start_px and start_px > 0:
            for p in history:
                day = str(p.get("ts") or "")[:10]
                px = p.get("price")
                if px is None:
                    px = price_by_day.get(day)
                if px is None:
                    continue
                p["bh_equity"] = round(start_eq * (float(px) / start_px), 2)

    sum_bot = equity_summary(history)
    paired = [p for p in history if p.get("bh_equity") is not None]
    # Alpha only on overlapping bot+BH points so windows match.
    sum_bh = equity_summary([{"equity": p["bh_equity"]} for p in paired]) if len(paired) >= 2 else {"n": 0}
    sum_bot_vs_bh = equity_summary(paired) if len(paired) >= 2 else sum_bot
    alpha = None
    if sum_bot_vs_bh.get("n") and sum_bh.get("n"):
        alpha = round(float(sum_bot_vs_bh["ret_pct"]) - float(sum_bh["ret_pct"]), 2)

    bg = _load_bitget()
    return {
        "ok": True,
        "market": market,
        "source": source,
        "range": range_key,
        "bh": bh_on,
        "points": history,
        "summary": {
            **sum_bot,
            "bh_ret_pct": sum_bh.get("ret_pct"),
            "alpha_pct": alpha,
        },
        "bitget_usdt": bg.get("cash"),
        "scalp_running": bool(bg.get("running")),
    }



def api_candles(_: None = Depends(require_auth)) -> dict[str, Any]:
    status = _load_json(LOG_DIR / "status.json")
    state = _load_json(STATE_PATH)
    market = str(status.get("market") or state.get("market") or "KRW-BTC")
    timeframe = str(status.get("timeframe") or "1h")
    _kind, _unit, period = _tf_to_upbit(timeframe)
    candles = _fetch_upbit_candles(market, timeframe, count=200)
    trades = state.get("trades") or []
    if not isinstance(trades, list):
        trades = []
    markers = _trade_markers(trades[-80:], [int(c["time"]) for c in candles], period)
    return {
        "ok": True,
        "market": market,
        "timeframe": timeframe,
        "period_seconds": period,
        "candles": candles,
        "markers": markers,
    }


app.add_api_route(_p("/healthz"), healthz, methods=["GET"])
app.add_api_route(_p("/"), index, methods=["GET"], response_class=HTMLResponse)
app.add_api_route(_p("/equity"), equity_page, methods=["GET"], response_class=HTMLResponse)
app.add_api_route(_p("/login"), login, methods=["POST"])
app.add_api_route(_p("/logout"), logout, methods=["POST"])
app.add_api_route(_p("/api/status"), api_status, methods=["GET"])
app.add_api_route(_p("/api/candles"), api_candles, methods=["GET"])
app.add_api_route(_p("/api/equity"), api_equity, methods=["GET"])

if BASE_PATH:
    app.add_api_route("/healthz", healthz, methods=["GET"])
    app.add_api_route("/", index, methods=["GET"], response_class=HTMLResponse)
    app.add_api_route("/equity", equity_page, methods=["GET"], response_class=HTMLResponse)
    app.add_api_route("/login", login, methods=["POST"])
    app.add_api_route("/logout", logout, methods=["POST"])
    app.add_api_route("/api/status", api_status, methods=["GET"])
    app.add_api_route("/api/candles", api_candles, methods=["GET"])
    app.add_api_route("/api/equity", api_equity, methods=["GET"])
    app.mount(_p("/static"), StaticFiles(directory=str(STATIC)), name="static_base")
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static_root")
else:
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
