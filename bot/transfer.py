"""Semi-automatic cross-exchange transfer (Telegram approve-to-execute)."""

from __future__ import annotations

import json
import logging
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from bot.config import Settings

logger = logging.getLogger(__name__)

PENDING_NAME = "transfer_pending.json"
HISTORY_NAME = "transfer_history.jsonl"


@dataclass(frozen=True)
class TransferRequest:
    code: str
    direction: str  # upbit_to_bitget | bitget_to_upbit
    coin: str
    amount: float
    chain: str
    created_at: float
    status: str = "pending"  # pending | executed | cancelled | failed
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "direction": self.direction,
            "coin": self.coin,
            "amount": self.amount,
            "chain": self.chain,
            "created_at": self.created_at,
            "status": self.status,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TransferRequest:
        return cls(
            code=str(raw["code"]),
            direction=str(raw["direction"]),
            coin=str(raw["coin"]).upper(),
            amount=float(raw["amount"]),
            chain=str(raw["chain"]),
            created_at=float(raw["created_at"]),
            status=str(raw.get("status") or "pending"),
            detail=str(raw.get("detail") or ""),
        )


def _pending_path(settings: Settings) -> Path:
    return settings.state_path.parent / PENDING_NAME


def _history_path(settings: Settings) -> Path:
    return settings.state_path.parent / HISTORY_NAME


def load_pending(settings: Settings) -> TransferRequest | None:
    path = _pending_path(settings)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        req = TransferRequest.from_dict(raw)
        if req.status != "pending":
            return None
        return req
    except Exception:
        logger.exception("transfer pending load failed")
        return None


def save_pending(settings: Settings, req: TransferRequest | None) -> None:
    path = _pending_path(settings)
    if req is None:
        if path.exists():
            path.unlink()
        return
    path.write_text(json.dumps(req.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def _append_history(settings: Settings, req: TransferRequest) -> None:
    path = _history_path(settings)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(req.to_dict(), ensure_ascii=False) + "\n")


def parse_direction(token: str) -> str | None:
    t = token.strip().lower().replace(" ", "")
    aliases = {
        "upbit->bitget": "upbit_to_bitget",
        "upbit→bitget": "upbit_to_bitget",
        "u2b": "upbit_to_bitget",
        "업비트->빗겟": "upbit_to_bitget",
        "업비트→빗겟": "upbit_to_bitget",
        "bitget->upbit": "bitget_to_upbit",
        "bitget→upbit": "bitget_to_upbit",
        "b2u": "bitget_to_upbit",
        "빗겟->업비트": "bitget_to_upbit",
        "빗겟→업비트": "bitget_to_upbit",
    }
    return aliases.get(t)


# Prefer lowest-fee networks for cross-exchange USDT (Tron TRC20 ≪ ERC20).
_CHEAPEST_CHAIN: dict[str, str] = {
    "USDT": "TRC20",
    "USDC": "TRC20",
    "TRX": "TRC20",
}

_CHAIN_ALIASES: dict[str, str] = {
    "TRON": "TRC20",
    "TRX": "TRC20",
    "TRC-20": "TRC20",
    "TRC20": "TRC20",
    "ETH": "ERC20",
    "ETHEREUM": "ERC20",
    "ERC-20": "ERC20",
    "ERC20": "ERC20",
    "BSC": "BEP20",
    "BNB": "BEP20",
    "BEP20": "BEP20",
    "BEP-20": "BEP20",
    "POLYGON": "POLYGON",
    "MATIC": "POLYGON",
    "BTC": "BTC",
    "BITCOIN": "BTC",
}


def normalize_chain(raw: str | None, coin: str, default: str) -> tuple[str, str | None]:
    """Return (chain, note). Always pick cheapest for known coins (e.g. USDT→TRC20)."""
    coin_u = coin.upper()
    preferred = _CHEAPEST_CHAIN.get(coin_u) or (default or "TRC20").strip()
    if not raw or not str(raw).strip():
        return preferred, None

    key = str(raw).strip().upper().replace(" ", "")
    mapped = _CHAIN_ALIASES.get(key, key)
    if coin_u in _CHEAPEST_CHAIN and mapped != preferred:
        note = f"수수료 절감을 위해 {mapped} 대신 {preferred}(최저수수료)로 고정했습니다."
        return preferred, note
    return mapped, None


def request_transfer(
    settings: Settings,
    *,
    direction: str,
    coin: str,
    amount: float,
    chain: str | None = None,
) -> str:
    if not settings.transfer_enabled:
        return (
            "이체가 꺼져 있습니다.\n"
            "TRANSFER_ENABLED=true 와 TRANSFER_CONFIRM=I_UNDERSTAND_TRANSFER_RISK 설정 후\n"
            "거래소 API에 출금 권한+IP를 열어 주세요."
        )
    if not settings.transfer_allowed:
        return "TRANSFER_CONFIRM 문구가 맞지 않아 이체를 막을 수 없습니다."
    if amount <= 0:
        return "수량은 0보다 커야 합니다."
    if settings.transfer_max_amount > 0 and amount > settings.transfer_max_amount:
        return f"한도 초과 — 최대 {settings.transfer_max_amount} 까지 가능합니다."

    coin_u = coin.upper()
    chain_u, chain_note = normalize_chain(
        chain, coin_u, settings.transfer_default_chain or "TRC20"
    )
    if direction == "upbit_to_bitget":
        dest = settings.transfer_whitelist_bitget.get(coin_u)
        if not dest:
            return (
                f"Bitget {coin_u} 화이트리스트 주소가 없습니다.\n"
                f"TRANSFER_WHITELIST_BITGET_{coin_u}=주소 를 .env에 넣으세요."
            )
    elif direction == "bitget_to_upbit":
        dest = settings.transfer_whitelist_upbit.get(coin_u)
        if not dest:
            return (
                f"Upbit {coin_u} 화이트리스트 주소가 없습니다.\n"
                f"TRANSFER_WHITELIST_UPBIT_{coin_u}=주소 를 .env에 넣으세요."
            )
    else:
        return "방향이 올바르지 않습니다. 예: upbit->bitget"

    existing = load_pending(settings)
    if existing:
        return (
            f"이미 대기 중인 이체가 있습니다: {existing.code}\n"
            f"/이체승인 {existing.code} 또는 /이체취소"
        )

    code = secrets.token_hex(3).upper()
    req = TransferRequest(
        code=code,
        direction=direction,
        coin=coin_u,
        amount=amount,
        chain=chain_u,
        created_at=time.time(),
    )
    save_pending(settings, req)
    arrow = "Upbit → Bitget" if direction == "upbit_to_bitget" else "Bitget → Upbit"
    lines = [
        "======= 이체 요청 (미실행) =======",
        f"코드: {code}",
        f"방향: {arrow}",
        f"자산: {amount} {coin_u}",
        f"체인: {chain_u} (최저수수료 우선)",
        f"목적지(화이트리스트): {dest[:8]}…{dest[-6:]}",
    ]
    if chain_note:
        lines.append(f"참고: {chain_note}")
    lines.extend(
        [
            "",
            f"실행: /이체승인 {code}",
            "취소: /이체취소",
            "===============================",
        ]
    )
    return "\n".join(lines)


def cancel_transfer(settings: Settings) -> str:
    req = load_pending(settings)
    if not req:
        return "대기 중인 이체가 없습니다."
    cancelled = TransferRequest(
        code=req.code,
        direction=req.direction,
        coin=req.coin,
        amount=req.amount,
        chain=req.chain,
        created_at=req.created_at,
        status="cancelled",
        detail="user_cancel",
    )
    _append_history(settings, cancelled)
    save_pending(settings, None)
    return f"이체 요청 {req.code} 를 취소했습니다."


def approve_transfer(settings: Settings, code: str) -> str:
    if not settings.transfer_allowed:
        return "이체 설정이 꺼져 있거나 CONFIRM 문구가 맞지 않습니다."
    req = load_pending(settings)
    if not req:
        return "대기 중인 이체가 없습니다."
    if req.code.upper() != code.strip().upper():
        return "승인 코드가 일치하지 않습니다."
    if time.time() - req.created_at > settings.transfer_ttl_sec:
        save_pending(settings, None)
        return "요청이 만료되었습니다. 다시 /이체요청 하세요."

    try:
        detail = _execute(settings, req)
        done = TransferRequest(
            code=req.code,
            direction=req.direction,
            coin=req.coin,
            amount=req.amount,
            chain=req.chain,
            created_at=req.created_at,
            status="executed",
            detail=detail,
        )
        _append_history(settings, done)
        save_pending(settings, None)
        return f"이체 실행됨 ({req.code})\n{detail}"
    except Exception as e:
        logger.exception("transfer execute failed")
        failed = TransferRequest(
            code=req.code,
            direction=req.direction,
            coin=req.coin,
            amount=req.amount,
            chain=req.chain,
            created_at=req.created_at,
            status="failed",
            detail=f"{type(e).__name__}: {e}",
        )
        _append_history(settings, failed)
        # keep pending so user can retry or cancel
        return f"이체 실패: {type(e).__name__}: {e}\n/이체취소 또는 원인 수정 후 /이체승인 {req.code}"


def upbit_net_type(coin: str, chain: str) -> str:
    """Map our chain labels to Upbit withdraw net_type values."""
    coin_u = coin.upper()
    chain_u = chain.upper().replace(" ", "")
    # Upbit USDT Tron network is net_type=TRX (not TRC20).
    if coin_u == "USDT" and chain_u in {"TRC20", "TRON", "TRX", "TRC-20"}:
        return "TRX"
    if coin_u == "USDC" and chain_u in {"TRC20", "TRON", "TRX", "TRC-20"}:
        return "TRX"
    return chain


def _execute(settings: Settings, req: TransferRequest) -> str:
    if req.direction == "upbit_to_bitget":
        address = settings.transfer_whitelist_bitget[req.coin]
        if not settings.upbit_access_key or not settings.upbit_secret_key:
            raise RuntimeError("UPBIT keys missing")
        from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

        net = upbit_net_type(req.coin, req.chain)
        client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
        try:
            result = client.withdraw_coin(
                currency=req.coin,
                amount=req.amount,
                address=address,
                net_type=net,
            )
        finally:
            client.close()
        return f"Upbit withdraw uuid={result.get('uuid') or result} net_type={net}"

    if req.direction == "bitget_to_upbit":
        address = settings.transfer_whitelist_upbit[req.coin]
        if not settings.bitget_ready:
            raise RuntimeError("BITGET keys missing")
        from bot.bitget_client import BitgetPrivate  # noqa: PLC0415

        client = BitgetPrivate(
            settings.bitget_api_key,
            settings.bitget_secret_key,
            settings.bitget_passphrase,
            paper_trading=settings.bitget_paper_trading,
        )
        try:
            result = client.withdraw(
                coin=req.coin,
                amount=str(req.amount),
                address=address,
                chain=req.chain,
            )
        finally:
            client.close()
        return f"Bitget withdraw={result}"

    raise RuntimeError(f"unknown direction {req.direction}")


# --- Auto funding (strategy-triggered, no Telegram approve) ---

FUNDING_NAME = "bitget_funding.json"
COOLDOWN_NAME = "transfer_auto_cooldown.json"


def _funding_path(settings: Settings) -> Path:
    return settings.state_path.with_name(FUNDING_NAME)


def _cooldown_path(settings: Settings) -> Path:
    return settings.state_path.parent / COOLDOWN_NAME


def load_funding_intent(settings: Settings) -> dict[str, Any] | None:
    path = _funding_path(settings)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("status") != "awaiting_deposit":
            return None
        return raw
    except Exception:
        logger.exception("funding intent load failed")
        return None


def save_funding_intent(settings: Settings, payload: dict[str, Any] | None) -> None:
    path = _funding_path(settings)
    if payload is None:
        if path.exists():
            path.unlink()
        return
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _cooldown_ok(settings: Settings) -> tuple[bool, str]:
    path = _cooldown_path(settings)
    if not path.exists():
        return True, ""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        last = float(raw.get("last_at") or 0)
        left = settings.transfer_cooldown_sec - (time.time() - last)
        if left > 0:
            return False, f"이체 쿨다운 {int(left)}초 남음"
    except Exception:
        return True, ""
    return True, ""


def _mark_cooldown(settings: Settings) -> None:
    path = _cooldown_path(settings)
    path.write_text(
        json.dumps({"last_at": time.time()}, ensure_ascii=False),
        encoding="utf-8",
    )


def _upbit_usdt_ticker() -> float:
    with httpx.Client(timeout=15.0) as client:
        resp = client.get("https://api.upbit.com/v1/ticker", params={"markets": "KRW-USDT"})
        resp.raise_for_status()
        rows = resp.json()
        return float(rows[0]["trade_price"])


def ensure_upbit_usdt(
    settings: Settings,
    *,
    amount: float,
    buy_from_krw: bool,
) -> str:
    """Make sure Upbit has enough USDT to withdraw; optionally market-buy from KRW."""
    if not settings.upbit_access_key or not settings.upbit_secret_key:
        raise RuntimeError("UPBIT keys missing for auto funding")
    from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

    client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
    notes: list[str] = []
    try:
        have = client.available_balance("USDT")
        if have + 1e-8 >= amount:
            return f"Upbit USDT 충분 ({have:.4f})"
        need = amount - have
        if not buy_from_krw:
            raise RuntimeError(f"Upbit USDT 부족 have={have:.4f} need={amount:.4f}")
        px = _upbit_usdt_ticker()
        # price order in KRW; pad 1.5% for fee/slippage
        krw = int(need * px * 1.015) + 1
        krw_bal = client.available_balance("KRW")
        if krw_bal < krw:
            raise RuntimeError(
                f"Upbit KRW 부족 — USDT {need:.4f} 매수에 약 {krw}원 필요, 보유 {krw_bal:.0f}원"
            )
        oid = client.make_identifier("usdtbuy")
        order = client.place_market_buy("KRW-USDT", float(krw), identifier=oid)
        client.wait_order(uuid_str=str(order.get("uuid") or ""), identifier=oid, timeout_sec=20)
        have2 = client.available_balance("USDT")
        if have2 + 1e-8 < amount:
            raise RuntimeError(f"KRW-USDT 매수 후에도 USDT 부족 have={have2:.4f} need={amount:.4f}")
        notes.append(f"KRW-USDT 매수 {krw}원 → USDT≈{have2:.4f}")
        return "; ".join(notes)
    finally:
        client.close()


def auto_fund_bitget_from_upbit(
    settings: Settings,
    *,
    amount: float,
    coin: str = "USDT",
    chain: str | None = None,
    buy_usdt_from_krw: bool = True,
    reason: str = "",
) -> str:
    """Execute Upbit→Bitget withdraw immediately (no Telegram approve)."""
    if not settings.transfer_allowed:
        raise RuntimeError(
            "자동 이체 OFF — TRANSFER_ENABLED=true + TRANSFER_CONFIRM=I_UNDERSTAND_TRANSFER_RISK"
        )
    if settings.transfer_max_amount <= 0:
        raise RuntimeError("자동 이체는 TRANSFER_MAX_AMOUNT>0 필수")
    if amount <= 0:
        raise RuntimeError("이체 수량이 0 이하")
    if amount > settings.transfer_max_amount + 1e-12:
        raise RuntimeError(
            f"이체액 {amount} > TRANSFER_MAX_AMOUNT {settings.transfer_max_amount}"
        )

    ok, msg = _cooldown_ok(settings)
    if not ok:
        raise RuntimeError(msg)

    coin_u = coin.upper()
    chain_u, _ = normalize_chain(chain, coin_u, settings.transfer_default_chain or "TRC20")
    dest = settings.transfer_whitelist_bitget.get(coin_u)
    if not dest:
        raise RuntimeError(f"TRANSFER_WHITELIST_BITGET_{coin_u} 미설정")

    prep = ensure_upbit_usdt(settings, amount=amount, buy_from_krw=buy_usdt_from_krw)
    req = TransferRequest(
        code=f"AUTO{secrets.token_hex(2).upper()}",
        direction="upbit_to_bitget",
        coin=coin_u,
        amount=amount,
        chain=chain_u,
        created_at=time.time(),
        status="pending",
        detail=reason or "strategy_auto_fund",
    )
    detail = _execute(settings, req)
    done = TransferRequest(
        code=req.code,
        direction=req.direction,
        coin=req.coin,
        amount=req.amount,
        chain=req.chain,
        created_at=req.created_at,
        status="executed",
        detail=f"{prep} | {detail}",
    )
    _append_history(settings, done)
    _mark_cooldown(settings)
    logger.warning(
        "AUTO TRANSFER executed code=%s amount=%s %s chain=%s reason=%s",
        req.code,
        amount,
        coin_u,
        chain_u,
        reason,
    )
    return f"{prep}\n{detail}"
