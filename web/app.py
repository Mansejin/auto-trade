from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
STATE_PATH = Path(os.getenv("STATE_PATH", "/app/data/state.json"))
RISK_PATH = Path(os.getenv("RISK_PATH", "/app/data/risk.json"))
TOKEN = os.getenv("DASHBOARD_TOKEN", "").strip()
BASE_PATH = os.getenv("BASE_PATH", "").strip().rstrip("/")
COOKIE_NAME = "desk_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 14

STATIC = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Auto-Trade Desk", docs_url=None, redoc_url=None)


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


def _set_auth_cookie(resp: Response, value: str) -> None:
    resp.set_cookie(
        COOKIE_NAME,
        value,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path=BASE_PATH or "/",
        secure=bool(BASE_PATH),
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


def healthz() -> dict[str, str]:
    return {"ok": "1", "base_path": BASE_PATH or "/"}


def index(
    request: Request,
    desk_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Response:
    if _authorized(desk_token) or _authorized(request.query_params.get("token")):
        if request.query_params.get("token") and not desk_token:
            resp = RedirectResponse(_p("/"), status_code=302)
            _set_auth_cookie(resp, request.query_params.get("token") or "")
            return resp
        return FileResponse(STATIC / "index.html")
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

    trades = state.get("trades") or []
    recent = trades[-8:] if isinstance(trades, list) else []

    market = str(status.get("market") or state.get("market") or "KRW-BTC")
    tv_symbol = "UPBIT:BTCKRW"
    if market.startswith("KRW-"):
        base = market.split("-", 1)[1]
        tv_symbol = f"UPBIT:{base}KRW"

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
    }


app.add_api_route(_p("/healthz"), healthz, methods=["GET"])
app.add_api_route(_p("/"), index, methods=["GET"], response_class=HTMLResponse)
app.add_api_route(_p("/login"), login, methods=["POST"])
app.add_api_route(_p("/logout"), logout, methods=["POST"])
app.add_api_route(_p("/api/status"), api_status, methods=["GET"])

if BASE_PATH:
    app.add_api_route("/healthz", healthz, methods=["GET"])
    app.add_api_route("/", index, methods=["GET"], response_class=HTMLResponse)
    app.add_api_route("/login", login, methods=["POST"])
    app.add_api_route("/logout", logout, methods=["POST"])
    app.add_api_route("/api/status", api_status, methods=["GET"])
    app.mount(_p("/static"), StaticFiles(directory=str(STATIC)), name="static_base")
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static_root")
else:
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
