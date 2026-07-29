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
    "TRX": "TRX",
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
    if coin_u == "TRX":
        chain_u = "TRX"
    if direction == "upbit_to_bitget":
        dest = bitget_whitelist_address(settings, coin_u)
        if not dest:
            return (
                f"Bitget {coin_u} 화이트리스트 주소가 없습니다.\n"
                f"TRANSFER_WHITELIST_BITGET_{coin_u}=주소 를 .env에 넣으세요.\n"
                f"(TRX는 TRANSFER_WHITELIST_BITGET_USDT 트론 주소 alias 가능)"
            )
    elif direction == "bitget_to_upbit":
        if coin_u == "TRX":
            chain_u = "TRX"
        dest = upbit_whitelist_address(settings, coin_u)
        if not dest:
            return (
                f"Upbit {coin_u} 화이트리스트 주소가 없습니다.\n"
                f"TRANSFER_WHITELIST_UPBIT_{coin_u}=주소 를 .env에 넣으세요.\n"
                f"(TRX는 TRANSFER_WHITELIST_UPBIT_USDT 트론 주소 alias 가능)"
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
        if req.direction == "upbit_to_bitget":
            _rebase_upbit_risk_after_withdraw(settings, coin=req.coin, amount=req.amount)
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
    if coin_u == "TRX":
        return "TRX"
    # Upbit USDT Tron network is net_type=TRX (not TRC20).
    if coin_u == "USDT" and chain_u in {"TRC20", "TRON", "TRX", "TRC-20"}:
        return "TRX"
    if coin_u == "USDC" and chain_u in {"TRC20", "TRON", "TRX", "TRC-20"}:
        return "TRX"
    return chain_u or chain


def _whitelist_address(table: dict[str, str], coin: str) -> str | None:
    """Resolve address; TRX↔USDT Tron address may alias."""
    coin_u = coin.upper()
    return table.get(coin_u) or (
        table.get("USDT") if coin_u == "TRX" else table.get("TRX") if coin_u == "USDT" else None
    )


def bitget_whitelist_address(settings: Settings, coin: str) -> str | None:
    return _whitelist_address(settings.transfer_whitelist_bitget, coin)


def upbit_whitelist_address(settings: Settings, coin: str) -> str | None:
    return _whitelist_address(settings.transfer_whitelist_upbit, coin)


def _bitget_client(settings: Settings):
    if not settings.bitget_ready:
        raise RuntimeError("BITGET keys missing")
    from bot.bitget_client import BitgetPrivate  # noqa: PLC0415

    return BitgetPrivate(
        settings.bitget_api_key,
        settings.bitget_secret_key,
        settings.bitget_passphrase,
        paper_trading=settings.bitget_paper_trading,
    )


def _execute(settings: Settings, req: TransferRequest) -> str:
    if req.direction == "upbit_to_bitget":
        address = bitget_whitelist_address(settings, req.coin)
        if not address:
            raise RuntimeError(f"TRANSFER_WHITELIST_BITGET_{req.coin} (or TRX/USDT alias) missing")
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
        address = upbit_whitelist_address(settings, req.coin)
        if not address:
            raise RuntimeError(f"TRANSFER_WHITELIST_UPBIT_{req.coin} (or TRX/USDT alias) missing")
        if not settings.bitget_ready:
            raise RuntimeError("BITGET keys missing")
        client = _bitget_client(settings)
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


def _upbit_ticker(market: str) -> float:
    with httpx.Client(timeout=15.0) as client:
        resp = client.get("https://api.upbit.com/v1/ticker", params={"markets": market})
        resp.raise_for_status()
        rows = resp.json()
        return float(rows[0]["trade_price"])


def ensure_upbit_coin(
    settings: Settings,
    *,
    coin: str,
    amount: float,
    buy_from_krw: bool,
) -> str:
    """Ensure Upbit has enough `coin`; optionally market-buy from KRW."""
    coin_u = coin.upper()
    if not settings.upbit_access_key or not settings.upbit_secret_key:
        raise RuntimeError("UPBIT keys missing for auto funding")
    from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

    market = f"KRW-{coin_u}"
    client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
    try:
        have = client.available_balance(coin_u)
        if have + 1e-8 >= amount:
            return f"Upbit {coin_u} 충분 ({have:.6f})"
        need = amount - have
        if not buy_from_krw:
            raise RuntimeError(f"Upbit {coin_u} 부족 have={have:.6f} need={amount:.6f}")
        px = _upbit_ticker(market)
        pad = 1.02 if coin_u == "TRX" else 1.015
        krw = int(need * px * pad) + 1
        krw_bal = client.available_balance("KRW")
        if krw_bal < krw:
            raise RuntimeError(
                f"Upbit KRW 부족 — {coin_u} {need:.6f} 매수에 약 {krw}원 필요, 보유 {krw_bal:.0f}원"
            )
        oid = client.make_identifier(f"{coin_u.lower()[:4]}buy")
        order = client.place_market_buy(market, float(krw), identifier=oid)
        client.wait_order(uuid_str=str(order.get("uuid") or ""), identifier=oid, timeout_sec=25)
        have2 = client.available_balance(coin_u)
        if have2 + 1e-8 < amount:
            raise RuntimeError(f"{market} 매수 후에도 {coin_u} 부족 have={have2:.6f} need={amount:.6f}")
        return f"{market} 매수 {krw}원 → {coin_u}≈{have2:.6f}"
    finally:
        client.close()


def plan_trx_withdraw_amount(*, top_up_krw: float, transfer_max: float) -> tuple[float, float]:
    """Convert KRW budget to withdrawable TRX amount (minus Upbit fee buffer)."""
    px = _upbit_ticker("KRW-TRX")
    fee = 1.0  # Upbit TRX withdraw fee (approx)
    raw = max(0.0, (top_up_krw / px) - fee - 0.01)
    if transfer_max > 0:
        raw = min(raw, transfer_max)
    amount = round(raw, 6)
    if amount < 1.0:
        raise RuntimeError(f"TRX 이체 수량 너무 작음: {amount} (예산 {top_up_krw}원)")
    return amount, px


def auto_fund_bitget_from_upbit(
    settings: Settings,
    *,
    amount: float,
    coin: str = "TRX",
    chain: str | None = None,
    buy_from_krw: bool = True,
    buy_usdt_from_krw: bool | None = None,
    reason: str = "",
) -> str:
    """Execute Upbit→Bitget withdraw immediately (no Telegram approve)."""
    if buy_usdt_from_krw is not None:
        buy_from_krw = buy_usdt_from_krw
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
    default_chain = "TRX" if coin_u == "TRX" else (settings.transfer_default_chain or "TRC20")
    chain_u, _ = normalize_chain(chain, coin_u, default_chain)
    if coin_u == "TRX":
        chain_u = "TRX"
    if not bitget_whitelist_address(settings, coin_u):
        raise RuntimeError(
            f"TRANSFER_WHITELIST_BITGET_{coin_u} 미설정 (TRX는 USDT 트론 주소 alias 가능)"
        )

    fee_buf = 1.0 if coin_u == "TRX" else 0.0
    need_on_upbit = amount + fee_buf + 0.01
    prep = ensure_upbit_coin(
        settings, coin=coin_u, amount=need_on_upbit, buy_from_krw=buy_from_krw
    )
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
    _rebase_upbit_risk_after_withdraw(settings, coin=coin_u, amount=amount)
    logger.warning(
        "AUTO TRANSFER executed code=%s amount=%s %s chain=%s reason=%s",
        req.code,
        amount,
        coin_u,
        chain_u,
        reason,
    )
    return f"{prep}\n{detail}"



def _rebase_upbit_risk_after_withdraw(settings: Settings, *, coin: str, amount: float) -> None:
    """After Upbit on-chain withdraw, lower Upbit bot day-start equity by KRW value."""
    try:
        from bot.risk import (  # noqa: PLC0415
            apply_external_outflow,
            clear_daily_loss_halt,
            load_risk,
            save_risk,
        )

        upbit_state = settings.state_path.with_name("state.json")
        px = _upbit_ticker(f"KRW-{coin.upper()}") if coin.upper() != "KRW" else 1.0
        outflow_krw = float(amount) * float(px)
        # Upbit LIVE integrity uses upbit secret even when called from bitget bot.
        key = settings.upbit_secret_key or ""
        risk = load_risk(upbit_state, integrity_key=key)
        risk = apply_external_outflow(risk, outflow_krw)
        risk = clear_daily_loss_halt(risk)
        save_risk(upbit_state, risk, integrity_key=key)
        logger.info(
            "Upbit risk rebased after withdraw coin=%s amount=%s ~%s KRW",
            coin,
            amount,
            round(outflow_krw),
        )
    except Exception:
        logger.exception("Upbit risk rebase after withdraw failed")

def convert_bitget_trx_to_usdt(settings: Settings, *, min_trx: float = 1.0) -> str:
    """Sell Bitget TRX→USDT on UTA spot. UTA equity is shared with futures."""
    client = _bitget_client(settings)
    try:
        trx = client.spot_available("TRX")
        if trx < min_trx:
            return f"Bitget TRX 부족({trx:.6f}) — 환전 스킵"
        qty = round(max(0.0, trx - 0.01), 2)
        if qty < min_trx:
            return f"Bitget TRX dust only ({trx:.6f})"
        before = client.available_usdt()
        order = client.place_order(
            category="SPOT",
            symbol="TRXUSDT",
            side="sell",
            order_type="market",
            qty=str(qty),
        )
        after = client.available_usdt()
        return (
            f"Bitget TRX→USDT 환전 qty={qty} order={order.get('orderId') or order} "
            f"USDT {before:.4f}→{after:.4f} (UTA 통합=선물 사용 가능)"
        )
    finally:
        client.close()


def convert_bitget_usdt_to_trx(settings: Settings, *, usdt_budget: float) -> str:
    """Buy TRX with USDT on Bitget UTA spot (for Bitget→Upbit bridge)."""
    if usdt_budget <= 0:
        raise RuntimeError("USDT budget must be > 0")
    client = _bitget_client(settings)
    try:
        avail = client.available_usdt()
        spend = min(avail, usdt_budget)
        if spend < 1.0:
            raise RuntimeError(f"Bitget USDT 부족 avail={avail:.4f} need≈{usdt_budget:.4f}")
        before = client.spot_available("TRX")
        # Bitget UTA place-order qty is base size — approx TRX qty from Upbit TRX/USDT.
        trx_krw = _upbit_ticker("KRW-TRX")
        usdt_krw = _upbit_ticker("KRW-USDT")
        trx_usdt = trx_krw / usdt_krw if usdt_krw > 0 else 0.0
        if trx_usdt <= 0:
            raise RuntimeError("TRX/USDT price unavailable")
        qty = round((spend * 0.98) / trx_usdt, 2)
        if qty < 1.0:
            raise RuntimeError(f"TRX buy qty too small: {qty}")
        order = client.place_order(
            category="SPOT",
            symbol="TRXUSDT",
            side="buy",
            order_type="market",
            qty=str(qty),
        )
        after = client.spot_available("TRX")
        return (
            f"Bitget USDT→TRX buy qty≈{qty} spend≤{spend:.4f} "
            f"order={order.get('orderId') or order} TRX {before:.4f}→{after:.4f}"
        )
    finally:
        client.close()


def ensure_upbit_krw(settings: Settings, *, target_krw: float, sell_bridge: bool = True) -> str:
    """Sell Upbit TRX/USDT into KRW until cash >= target (best-effort)."""
    if not settings.upbit_access_key or not settings.upbit_secret_key:
        raise RuntimeError("UPBIT keys missing")
    from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

    client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
    notes: list[str] = []
    try:
        krw = client.available_balance("KRW")
        if krw + 1e-6 >= target_krw:
            return f"Upbit KRW 충분 ({krw:,.0f} ≥ {target_krw:,.0f})"
        if not sell_bridge:
            raise RuntimeError(f"Upbit KRW 부족 have={krw:,.0f} need={target_krw:,.0f}")
        need = target_krw - krw
        # Prefer TRX then USDT
        for coin in ("TRX", "USDT"):
            if need <= 0:
                break
            bal = client.available_balance(coin)
            if bal <= 0:
                continue
            px = _upbit_ticker(f"KRW-{coin}")
            # sell enough for remaining need (+2% pad)
            want = min(bal, (need * 1.02) / px if px > 0 else 0.0)
            if coin == "TRX":
                want = round(want, 4)
            else:
                want = round(want, 6)
            if want <= 0:
                continue
            oid = client.make_identifier(f"{coin.lower()[:4]}sel")
            order = client.place_market_sell(f"KRW-{coin}", want, identifier=oid)
            client.wait_order(uuid_str=str(order.get("uuid") or ""), identifier=oid, timeout_sec=25)
            notes.append(f"KRW-{coin} 매도 {want}")
            krw = client.available_balance("KRW")
            need = max(0.0, target_krw - krw)
        krw2 = client.available_balance("KRW")
        notes.append(f"Upbit KRW {krw2:,.0f} (목표 {target_krw:,.0f})")
        if krw2 + 1e-6 < target_krw:
            notes.append("목표 미달 — Bitget 브릿지 입금 대기 후 재시도")
        return "; ".join(notes)
    finally:
        client.close()


def auto_fund_upbit_from_bitget(
    settings: Settings,
    *,
    top_up_krw: float,
    reason: str = "",
) -> str:
    """Bitget USDT→TRX → withdraw TRX to Upbit (no Telegram approve)."""
    if not settings.transfer_allowed:
        raise RuntimeError(
            "자동 이체 OFF — TRANSFER_ENABLED=true + TRANSFER_CONFIRM=I_UNDERSTAND_TRANSFER_RISK"
        )
    if settings.transfer_max_amount <= 0:
        raise RuntimeError("자동 이체는 TRANSFER_MAX_AMOUNT>0 필수")
    if top_up_krw <= 0:
        raise RuntimeError("top_up_krw must be > 0")

    ok, msg = _cooldown_ok(settings)
    if not ok:
        raise RuntimeError(msg)

    if not upbit_whitelist_address(settings, "TRX"):
        raise RuntimeError(
            "TRANSFER_WHITELIST_UPBIT_TRX (또는 USDT 트론 주소 alias) 미설정"
        )

    usdt_px = _upbit_ticker("KRW-USDT")
    usdt_budget = (top_up_krw / usdt_px) * 1.02 if usdt_px > 0 else 0.0
    prep = convert_bitget_usdt_to_trx(settings, usdt_budget=usdt_budget)

    client = _bitget_client(settings)
    try:
        trx = client.spot_available("TRX")
    finally:
        client.close()

    # leave dust; Bitget withdraw fee is exchange-side — keep small buffer
    amount = round(max(0.0, trx - 1.0), 6)
    if settings.transfer_max_amount > 0:
        amount = min(amount, settings.transfer_max_amount)
    if amount < 1.0:
        raise RuntimeError(f"Bitget TRX 출금 수량 부족: {amount} (after buy)")

    req = TransferRequest(
        code=f"AUTO{secrets.token_hex(2).upper()}",
        direction="bitget_to_upbit",
        coin="TRX",
        amount=amount,
        chain="TRX",
        created_at=time.time(),
        status="pending",
        detail=reason or "auto_fund_b2u",
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
        "AUTO TRANSFER B2U executed code=%s amount=%s TRX reason=%s",
        req.code,
        amount,
        reason,
    )
    return f"{prep}\n{detail}"
