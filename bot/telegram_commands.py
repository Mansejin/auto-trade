from __future__ import annotations

import json
import logging
import re
import shutil
import threading
import time
from pathlib import Path

import httpx

from bot.config import Settings
from bot.display import fmt_money, fmt_qty, fmt_quote, market_ko, mode_ko
from bot.telegram_notify import TelegramNotifier
from bot import transfer as xfer
from bot import rebalance as rebal

logger = logging.getLogger("bot.telegram.cmd")

HELP = """명령어 안내

조회 — 계좌·보유·최근 판단 보기
자산 — Upbit/Bitget 5:5 배분 현황
전략 — 지금 쓰는 전략 요약
로그 — 최근 상태 한 장 보기
서버 — 오라클 서버 상태
이체요청 <방향> <코인> <수량> [체인] — 반자동 이체 대기열
  예: 이체요청 upbit->bitget TRX 100
  방향: upbit->bitget | bitget->upbit
이체승인 <코드> / 이체취소
원화준비 <원> — Upbit KRW 목표 (제안→승인)
리밸런스 — 5:5±밴드 이탈 시 제안 (또는 강제 제안)
리밸런스승인 <코드> / 리밸런스취소
? — 이 안내"""


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _side_ko(side: str) -> str:
    return {"buy": "매수", "sell": "매도"}.get(str(side).lower(), str(side))


def _cmd_status(settings: Settings) -> str:
    mode = mode_ko("PAPER" if settings.paper else "LIVE")
    state = _load_state(settings.state_path)
    strategy_name = state.get("strategy") or settings.strategy_path.stem
    market = str(state.get("market") or "-")
    pos = state.get("position")
    trades = state.get("trades") or []

    lines = [
        "======= 계좌 / 봇 =======",
        f"거래소: {settings.exchange}",
        f"모드: {mode}",
        f"전략: {strategy_name}",
        f"파일: {settings.strategy_path.name}",
        f"종목: {market_ko(market) if market != '-' else '-'}",
        f"확인 주기: {settings.poll_seconds // 60}분마다",
    ]

    # LIVE only: hit private API. PAPER uses local state (avoid leaking keys usage).
    if (not settings.paper) and settings.exchange == "upbit" and settings.upbit_access_key and settings.upbit_secret_key:
        try:
            from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

            client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
            try:
                krw = client.available_balance("KRW")
                base = "BTC"
                if isinstance(market, str) and "-" in market:
                    base = market.split("-", 1)[1]
                coin = client.available_balance(base)
                lines.append(f"원화 잔고: {fmt_money(krw)}원")
                lines.append(f"{base} 잔고: {fmt_qty(coin)}")
            finally:
                client.close()
        except Exception as e:
            lines.append(f"업비트 잔고 조회 실패: {type(e).__name__}")
    elif (not settings.paper) and settings.exchange == "bitget" and settings.bitget_ready:
        try:
            from bot.bitget_client import BitgetPrivate  # noqa: PLC0415

            client = BitgetPrivate(
                settings.bitget_api_key,
                settings.bitget_secret_key,
                settings.bitget_passphrase,
                paper_trading=settings.bitget_paper_trading,
            )
            try:
                usdt = client.available_usdt(str(market).replace("-", "") if market != "-" else "BTCUSDT")
                lines.append(f"Bitget USDT(가용≈): {fmt_quote(usdt, 'USDT')}")
            finally:
                client.close()
        except Exception as e:
            lines.append(f"Bitget 잔고 조회 실패: {type(e).__name__}")
    else:
        cash = float(state.get("cash") or settings.paper_cash)
        if settings.exchange == "bitget":
            lines.append(f"모의 현금: {fmt_quote(cash, 'USDT')}")
        else:
            lines.append(f"모의 현금: {fmt_quote(cash, 'KRW')}")

    quote = "USDT" if settings.exchange == "bitget" else "KRW"
    if pos:
        lines.append(
            f"보유: {fmt_qty(float(pos.get('qty') or 0))}개 "
            f"(평균 {fmt_quote(float(pos.get('entry_price') or 0), quote)})"
        )
        lines.append(f"진입 시각: {pos.get('opened_at') or '-'}")
    else:
        lines.append("보유: 없음 (현금만)")

    lines.append(f"기록된 거래 수: {len(trades)}건")
    if trades:
        last = trades[-1]
        lines.append(
            f"최근 거래: {_side_ko(str(last.get('side')))} "
            f"{fmt_quote(float(last.get('price') or 0), quote)} "
            f"({last.get('ts') or '-'})"
        )

    latest = settings.log_dir / "latest_status.txt"
    if latest.exists():
        lines.append("")
        lines.append(latest.read_text(encoding="utf-8").strip())

    return "\n".join(lines)


def _cmd_strategy(settings: Settings) -> str:
    path = settings.strategy_path
    if not path.exists():
        return f"전략 파일이 없습니다: {path.name}"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"전략 파일을 읽지 못했습니다: {e}"
    return "\n".join(
        [
            "======= 전략 요약 =======",
            f"이름: {raw.get('name') or path.stem}",
            f"파일: {path.name}",
            f"종목: {market_ko(str(raw.get('market') or '-'))}",
            f"봉간격: {raw.get('timeframe')}",
            f"손절: {raw.get('stop_loss')}% / 익절: {raw.get('take_profit')}%",
            f"사용 지표: {len(raw.get('indicators') or [])}개",
            "========================",
        ]
    )


def _cmd_log(settings: Settings) -> str:
    latest = settings.log_dir / "latest_status.txt"
    if not latest.exists():
        return "아직 상태 기록이 없습니다. 다음 확인 주기를 기다려 주세요."
    return latest.read_text(encoding="utf-8").strip()


def _read_mem() -> tuple[int, int, int]:
    """Return (total, available, used) bytes from /proc/meminfo."""
    info: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(":"):
            info[parts[0][:-1]] = int(parts[1]) * 1024
    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", info.get("MemFree", 0))
    used = max(0, total - available)
    return total, available, used


def _fmt_bytes(n: int) -> str:
    mb = n / (1024 * 1024)
    if mb >= 1024:
        return f"{mb / 1024:.1f}GB"
    return f"{mb:.0f}MB"


def _cmd_server(_settings: Settings) -> str:
    try:
        load1, load5, load15 = Path("/proc/loadavg").read_text(encoding="utf-8").split()[:3]
    except Exception:
        load1 = load5 = load15 = "?"

    try:
        total, available, used = _read_mem()
        mem_line = (
            f"메모리: {_fmt_bytes(used)} 사용 / {_fmt_bytes(total)} "
            f"(여유 {_fmt_bytes(available)}, {used * 100 // total if total else 0}%)"
        )
    except Exception:
        mem_line = "메모리: 조회 실패"

    try:
        disk = shutil.disk_usage("/")
        disk_line = (
            f"디스크: {_fmt_bytes(disk.used)} 사용 / {_fmt_bytes(disk.total)} "
            f"({disk.used * 100 // disk.total}%)"
        )
    except Exception:
        disk_line = "디스크: 조회 실패"

    bot_line = "봇 프로세스: 동작 중"
    try:
        rss_kb = 0
        status = Path("/proc/self/status").read_text(encoding="utf-8")
        for line in status.splitlines():
            if line.startswith("VmRSS:"):
                rss_kb = int(line.split()[1])
                break
        bot_line = f"봇 메모리(대략): {_fmt_bytes(rss_kb * 1024)}"
    except Exception:
        pass

    mode = mode_ko("PAPER" if _settings.paper else "LIVE")
    return "\n".join(
        [
            "======= 서버 상태 =======",
            f"부하: {load1} / {load5} / {load15} (1·5·15분)",
            mem_line,
            disk_line,
            bot_line,
            f"거래 모드: {mode}",
            f"전략: {_settings.strategy_path.name}",
            f"확인 주기: {_settings.poll_seconds // 60}분",
            f"시각: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "========================",
        ]
    )


_CMD_COOLDOWN_SEC = 3.0
_last_cmd_at = 0.0


def handle_command(text: str, settings: Settings) -> str | None:
    global _last_cmd_at
    raw = text.strip()
    if not raw:
        return None
    # Allow both "/조회" and "조회"
    first = raw.split()[0]
    first = first.split("@", 1)[0]
    cmd = first.lower()
    if not cmd.startswith("/"):
        cmd = "/" + cmd

    known = {
        "/?",
        "/start",
        "/help",
        "/도움말",
        "/도움",
        "/조회",
        "/상태",
        "/status",
        "/bal",
        "/잔고",
        "/전략",
        "/strategy",
        "/로그",
        "/log",
        "/서버",
        "/server",
        "/상태서버",
        "/이체요청",
        "/이체승인",
        "/이체취소",
        "/transfer",
        "/xfer",
        "/자산",
        "/배분",
        "/원화준비",
        "/리밸런스",
        "/리밸런스승인",
        "/리밸런스취소",
    }
    if cmd in known or first.startswith("/") or first == "?":
        now = time.time()
        if now - _last_cmd_at < _CMD_COOLDOWN_SEC:
            return "잠시만요 — 명령은 3초에 한 번만 가능합니다."
        _last_cmd_at = now

    if cmd in {"/?", "/start", "/help", "/도움말", "/도움"}:
        return HELP
    if cmd in {"/조회", "/상태", "/status", "/bal", "/잔고"}:
        return _cmd_status(settings)
    if cmd in {"/전략", "/strategy"}:
        return _cmd_strategy(settings)
    if cmd in {"/로그", "/log"}:
        return _cmd_log(settings)
    if cmd in {"/서버", "/server", "/상태서버"}:
        return _cmd_server(settings)
    if cmd in {"/이체요청", "/transfer", "/xfer"}:
        return _cmd_transfer_request(raw, settings)
    if cmd in {"/이체승인"}:
        parts = raw.split()
        if len(parts) < 2:
            return "사용법: /이체승인 <코드>"
        return xfer.approve_transfer(settings, parts[1])
    if cmd in {"/이체취소"}:
        return xfer.cancel_transfer(settings)
    if cmd in {"/자산", "/배분"}:
        snap = rebal.snapshot_equity(settings)
        return rebal.format_snapshot(
            snap, target=settings.rebalance_target, band=settings.rebalance_band
        )
    if cmd in {"/원화준비"}:
        parts = raw.split()
        if len(parts) < 2:
            return "사용법: /원화준비 <원>  예: /원화준비 500000"
        try:
            amt = float(parts[1].replace(",", ""))
        except ValueError:
            return "금액은 숫자여야 합니다."
        return rebal.propose_krw_prepare(settings, amt)
    if cmd in {"/리밸런스"}:
        return rebal.propose_rebalance(settings, force=True, reason="telegram")
    if cmd in {"/리밸런스승인"}:
        parts = raw.split()
        if len(parts) < 2:
            return "사용법: /리밸런스승인 <코드>"
        return rebal.approve_pending(settings, parts[1])
    if cmd in {"/리밸런스취소"}:
        return rebal.cancel_pending(settings)
    if first.startswith("/") or first == "?":
        return f"모르는 명령입니다: {first}\n\n{HELP}"
    return None


def _cmd_transfer_request(raw: str, settings: Settings) -> str:
    # /이체요청 upbit->bitget USDT 50 [TRC20]
    parts = raw.split()
    if len(parts) < 4:
        return (
            "사용법: /이체요청 <방향> <코인> <수량> [체인]\n"
            "예: /이체요청 upbit->bitget USDT 50\n"
            "방향: upbit->bitget | bitget->upbit\n"
            "체인 생략 시 USDT는 TRC20(트론, 최저수수료) 고정"
        )
    direction = xfer.parse_direction(parts[1])
    if not direction:
        return "방향을 확인하세요. 예: upbit->bitget"
    coin = parts[2]
    try:
        amount = float(parts[3])
    except ValueError:
        return "수량은 숫자여야 합니다."
    chain = parts[4] if len(parts) >= 5 else None
    return xfer.request_transfer(
        settings, direction=direction, coin=coin, amount=amount, chain=chain
    )


def _redact_tg(text: str, token: str) -> str:
    """Keep bot tokens out of logs (httpx puts them in exception URLs)."""
    out = str(text)
    if token:
        out = out.replace(token, "***")
    return re.sub(r"bot\d+:[A-Za-z0-9_-]+", "bot***:***", out)


def _poll_loop(settings: Settings, notify: TelegramNotifier, stop: threading.Event) -> None:
    offset = 0
    # Build path without embedding the token in a reusable URL string for logs.
    token = settings.telegram_bot_token
    allowed = str(settings.telegram_chat_id)
    logger.info("텔레그램 명령 수신을 시작합니다.")

    with httpx.Client(timeout=40.0) as client:
        while not stop.is_set():
            try:
                resp = client.get(
                    f"https://api.telegram.org/bot{token}/getUpdates",
                    params={
                        "offset": offset,
                        "timeout": 25,
                        "allowed_updates": json.dumps(["message"]),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                for upd in data.get("result") or []:
                    offset = max(offset, int(upd.get("update_id", 0)) + 1)
                    msg = upd.get("message") or {}
                    chat = msg.get("chat") or {}
                    chat_id = str(chat.get("id") or "")
                    text = str(msg.get("text") or "")
                    if not text:
                        continue
                    if chat_id != allowed:
                        logger.warning("허용되지 않은 채팅 요청을 무시했습니다.")
                        continue
                    reply = handle_command(text, settings)
                    if reply:
                        notify.send(reply)
            except Exception as e:
                if stop.is_set():
                    break
                # Never logger.exception here — traceback includes tokenized URLs.
                logger.warning(
                    "텔레그램 수신 오류 — 잠시 후 다시 시도합니다: %s",
                    _redact_tg(e, token),
                )
                stop.wait(3)

    logger.info("텔레그램 명령 수신을 종료합니다.")


def start_command_listener(
    settings: Settings,
    notify: TelegramNotifier,
    stop: threading.Event,
) -> threading.Thread | None:
    if not notify.enabled:
        return None
    if not settings.telegram_commands_enabled:
        logger.info("텔레그램 명령 수신 비활성 (TELEGRAM_COMMANDS=false)")
        return None
    t = threading.Thread(
        target=_poll_loop,
        args=(settings, notify, stop),
        name="telegram-commands",
        daemon=True,
    )
    t.start()
    return t
