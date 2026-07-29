from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
STATE_PATH = Path(os.getenv("STATE_PATH", "/app/data/state.json"))
RISK_PATH = Path(os.getenv("RISK_PATH", "/app/data/risk.json"))
TOKEN = os.getenv("DASHBOARD_TOKEN", "").strip()
BASE_PATH = os.getenv("BASE_PATH", "").strip().rstrip("/")
COOKIE_NAME = "desk_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 14
LOGIN_WINDOW_SEC = 300
LOGIN_MAX_ATTEMPTS = 8
MIN_TOKEN_LEN = 32

# TradingView embed + same-origin API polling
CSP = (
    "default-src 'self'; "
    "script-src 'self' https://s3.tradingview.com; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' https://*.tradingview.com wss://*.tradingview.com; "
    "frame-src https://*.tradingview.com https://www.tradingview.com; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Auto-Trade Desk", docs_url=None, redoc_url=None)

_login_hits: dict[str, deque[float]] = defaultdict(deque)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        resp.headers.setdefault("Cache-Control", "no-store")
        resp.headers.setdefault("Content-Security-Policy", CSP)
        return resp


app.add_middleware(SecurityHeadersMiddleware)


def _p(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{BASE_PATH}{path}" if BASE_PATH else path


def _client_ip(request: Request) -> str:
    """Use proxy-set client IP only — never trust client-supplied X-Forwarded-For."""
    real_ip = (request.headers.get("x-real-ip") or "").strip()
    if real_ip:
        return real_ip[:64]
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _login_allowed(ip: str) -> bool:
    now = time.time()
    q = _login_hits[ip]
    while q and now - q[0] > LOGIN_WINDOW_SEC:
        q.popleft()
    return len(q) < LOGIN_MAX_ATTEMPTS


def _login_mark(ip: str) -> None:
    _login_hits[ip].append(time.time())


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


def _issue_csrf() -> str:
    if not TOKEN:
        return ""
    nonce = secrets.token_urlsafe(16)
    sig = hmac.new(TOKEN.encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{nonce}.{sig}"


def _verify_csrf(value: str | None) -> bool:
    if not TOKEN or not value:
        return False
    parts = value.rsplit(".", 1)
    if len(parts) != 2:
        return False
    nonce, sig = parts
    expected = hmac.new(TOKEN.encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


def _serve_html(name: str) -> HTMLResponse:
    raw = (STATIC / name).read_text(encoding="utf-8")
    html = raw.replace("{{CSRF}}", _issue_csrf())
    return HTMLResponse(html)


def _cookie_secure(request: Request) -> bool:
    xf = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    return request.url.scheme == "https" or xf == "https" or bool(BASE_PATH)


def _set_auth_cookie(resp: Response, value: str, *, secure: bool) -> None:
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
    # Do not accept ?token= — URLs leak via logs, history, and Referer.
    header = request.headers.get("Authorization", "")
    bearer = header[7:].strip() if header.lower().startswith("bearer ") else ""
    if not (_authorized(desk_token) or _authorized(bearer)):
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


def healthz() -> dict[str, str]:
    return {"ok": "1", "base_path": BASE_PATH or "/"}


def index(
    request: Request,
    desk_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Response:
    if _authorized(desk_token):
        return _serve_html("index.html")
    return _serve_html("login.html")


def login(request: Request, token: str = Form(...), csrf: str = Form(...)) -> Response:
    if not _verify_csrf(csrf):
        return HTMLResponse("Invalid request.", status_code=403)
    ip = _client_ip(request)
    if not _login_allowed(ip):
        return HTMLResponse("Too many login attempts. Try again later.", status_code=429)
    if not _authorized(token.strip()):
        _login_mark(ip)
        return RedirectResponse(_p("/?e=1"), status_code=303)
    resp = RedirectResponse(_p("/"), status_code=303)
    _set_auth_cookie(resp, token.strip(), secure=_cookie_secure(request))
    return resp


def logout(request: Request, csrf: str = Form(...)) -> Response:
    if not _verify_csrf(csrf):
        return HTMLResponse("Invalid request.", status_code=403)
    resp = RedirectResponse(_p("/"), status_code=303)
    _clear_auth_cookie(resp)
    return resp


def api_status(_: None = Depends(require_auth)) -> dict[str, Any]:
    status_path = LOG_DIR / "status.json"
    status = _load_json(status_path)
    state = _load_json(STATE_PATH)
    risk = _load_json(RISK_PATH)
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
        # Cap size to avoid huge log dumps over the API.
        latest_text = text_path.read_text(encoding="utf-8", errors="ignore")[:8000]

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
        # Expose operational flags only — omit verbose internal halt text if huge.
        status["risk"] = {
            "trading_halted": bool(risk.get("trading_halted")),
            "halt_buys_only": bool(risk.get("halt_buys_only")),
            "halt_reason": str(risk.get("halt_reason") or "")[:200],
            "consecutive_errors": risk.get("consecutive_errors"),
        }

    trades = state.get("trades") or []
    recent = trades[-8:] if isinstance(trades, list) else []

    market = str(status.get("market") or state.get("market") or "KRW-BTC")
    exchange = str(status.get("exchange") or state.get("exchange") or "upbit").lower()
    quote = str(status.get("quote_currency") or ("USDT" if exchange == "bitget" else "KRW")).upper()
    tv_symbol = "UPBIT:BTCKRW"
    if market.startswith("KRW-"):
        base = market.split("-", 1)[1]
        tv_symbol = f"UPBIT:{base}KRW"
    elif exchange == "bitget" or market.upper().endswith("USDT"):
        sym = market.upper().replace("-", "")
        if not sym.endswith("USDT"):
            sym = f"{sym}USDT"
        tv_symbol = f"BITGET:{sym}"

    # Normalize cash field for the desk ticker
    if status.get("cash") is None and status.get("usdt") is not None:
        status = {**status, "cash": status.get("usdt")}
    status.setdefault("quote_currency", quote)
    status.setdefault("exchange", exchange)

    return {
        "ok": True,
        "stale": stale,
        "mtime": mtime,
        "base_path": BASE_PATH or "",
        "status": status,
        "recent_trades": recent,
        "latest_text": latest_text,
        "tv_symbol": tv_symbol,
        "tv_interval": _tf_to_tv(str(status.get("timeframe") or "60")),
        "market": market,
        "timeframe": str(status.get("timeframe") or "1h"),
        "quote_currency": quote,
        "exchange": exchange,
    }


def _register(path: str, endpoint: Any, methods: list[str], **kwargs: Any) -> None:
    app.add_api_route(_p(path), endpoint, methods=methods, **kwargs)
    if BASE_PATH:
        app.add_api_route(path if path.startswith("/") else f"/{path}", endpoint, methods=methods, **kwargs)


_register("/healthz", healthz, ["GET"])
_register("/", index, ["GET"], response_class=HTMLResponse)
_register("/login", login, ["POST"])
_register("/logout", logout, ["POST"])
_register("/api/status", api_status, ["GET"])

if BASE_PATH:
    app.mount(_p("/static"), StaticFiles(directory=str(STATIC)), name="static_base")
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static_root")
else:
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.on_event("startup")
def _startup_checks() -> None:
    if not TOKEN:
        # Fail-closed: every page/API stays unauthorized.
        return
    if len(TOKEN) < MIN_TOKEN_LEN:
        raise RuntimeError(f"DASHBOARD_TOKEN must be at least {MIN_TOKEN_LEN} characters")
