"""Hybrid 50:50 treasury rebalance + KRW prepare (propose → Telegram approve)."""

from __future__ import annotations

import json
import logging
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bot.config import Settings
from bot import transfer as xfer

logger = logging.getLogger(__name__)

PENDING_NAME = "rebalance_pending.json"
ALERT_COOLDOWN_NAME = "rebalance_alert_cooldown.json"


@dataclass(frozen=True)
class EquitySnapshot:
    upbit_krw: float
    bitget_krw: float
    usdt_krw_px: float
    trx_krw_px: float
    detail: str

    @property
    def total_krw(self) -> float:
        return self.upbit_krw + self.bitget_krw

    @property
    def upbit_share(self) -> float:
        tot = self.total_krw
        return (self.upbit_krw / tot) if tot > 1e-6 else 0.5


def _pending_path(settings: Settings) -> Path:
    return settings.state_path.parent / PENDING_NAME


def _alert_cooldown_path(settings: Settings) -> Path:
    return settings.state_path.parent / ALERT_COOLDOWN_NAME


def load_pending(settings: Settings) -> dict[str, Any] | None:
    path = _pending_path(settings)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("status") != "pending":
            return None
        if time.time() - float(raw.get("created_at") or 0) > settings.transfer_ttl_sec:
            path.unlink(missing_ok=True)
            return None
        return raw
    except Exception:
        logger.exception("rebalance pending load failed")
        return None


def save_pending(settings: Settings, payload: dict[str, Any] | None) -> None:
    path = _pending_path(settings)
    if payload is None:
        if path.exists():
            path.unlink()
        return
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _alert_cooldown_ok(settings: Settings) -> bool:
    path = _alert_cooldown_path(settings)
    if not path.exists():
        return True
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        last = float(raw.get("last_at") or 0)
        return (time.time() - last) >= settings.rebalance_alert_cooldown_sec
    except Exception:
        return True


def _mark_alert_cooldown(settings: Settings) -> None:
    path = _alert_cooldown_path(settings)
    path.write_text(json.dumps({"last_at": time.time()}, ensure_ascii=False), encoding="utf-8")


def snapshot_equity(settings: Settings) -> EquitySnapshot:
    """Mark Upbit + Bitget liquid equity in KRW (bridge coins + cash; futures USDT equity)."""
    usdt_px = xfer._upbit_ticker("KRW-USDT")
    trx_px = xfer._upbit_ticker("KRW-TRX")
    notes: list[str] = []

    upbit = 0.0
    if settings.upbit_access_key and settings.upbit_secret_key:
        from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

        client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
        try:
            krw = client.available_balance("KRW")
            usdt = client.available_balance("USDT")
            trx = client.available_balance("TRX")
            btc = client.available_balance("BTC")
            btc_px = xfer._upbit_ticker("KRW-BTC") if btc > 1e-8 else 0.0
            upbit = krw + usdt * usdt_px + trx * trx_px + btc * btc_px
            notes.append(
                f"Upbit KRW={krw:.0f} USDT={usdt:.4f} TRX={trx:.2f} BTC={btc:.6f}"
            )
        finally:
            client.close()
    else:
        notes.append("Upbit keys missing")

    bitget = 0.0
    if settings.bitget_ready:
        from bot.bitget_client import BitgetPrivate  # noqa: PLC0415

        client = BitgetPrivate(
            settings.bitget_api_key,
            settings.bitget_secret_key,
            settings.bitget_passphrase,
            paper_trading=settings.bitget_paper_trading,
        )
        try:
            assets = client.account_assets()
            usdt_eq = 0.0
            try:
                usdt_eq = float(assets.get("usdtEquity") or 0.0)
            except (TypeError, ValueError):
                usdt_eq = 0.0
            if usdt_eq <= 0:
                usdt_eq = client.available_usdt()
            trx = client.spot_available("TRX")
            # usdtEquity already covers USDT/futures; add loose TRX if not in equity
            bitget = usdt_eq * usdt_px + trx * trx_px
            notes.append(f"Bitget usdtEq={usdt_eq:.4f} TRX={trx:.2f}")
        finally:
            client.close()
    else:
        notes.append("Bitget keys missing")

    return EquitySnapshot(
        upbit_krw=upbit,
        bitget_krw=bitget,
        usdt_krw_px=usdt_px,
        trx_krw_px=trx_px,
        detail="; ".join(notes),
    )


def format_snapshot(snap: EquitySnapshot, *, target: float, band: float) -> str:
    tot = snap.total_krw
    share = snap.upbit_share
    lo = target - band
    hi = target + band
    in_band = lo <= share <= hi
    return "\n".join(
        [
            "======= 자산 배분 =======",
            f"Upbit ≈ {snap.upbit_krw:,.0f}원 ({share * 100:.1f}%)",
            f"Bitget ≈ {snap.bitget_krw:,.0f}원 ({(1 - share) * 100:.1f}%)",
            f"합계 ≈ {tot:,.0f}원",
            f"목표 {target * 100:.0f}% ± {band * 100:.0f}%p "
            f"→ 허용 [{lo * 100:.0f}%, {hi * 100:.0f}%] "
            f"{'OK' if in_band else '이탈'}",
            snap.detail,
            "========================",
        ]
    )


def _plan_move_krw(snap: EquitySnapshot, *, target: float) -> tuple[str, float]:
    """Return (direction, move_krw). direction: upbit_to_bitget | bitget_to_upbit | none."""
    tot = snap.total_krw
    if tot < 1:
        return "none", 0.0
    target_upbit = tot * target
    delta = target_upbit - snap.upbit_krw  # + => need more on Upbit (pull from Bitget)
    if abs(delta) < 1:
        return "none", 0.0
    if delta > 0:
        return "bitget_to_upbit", delta
    return "upbit_to_bitget", -delta


def propose_rebalance(
    settings: Settings,
    *,
    force: bool = False,
    reason: str = "manual",
) -> str:
    if not settings.rebalance_enabled:
        return "리밸런스가 꺼져 있습니다. REBALANCE_ENABLED=true 설정 후 사용하세요."
    if not settings.transfer_allowed:
        return "이체 OFF — TRANSFER_ENABLED + TRANSFER_CONFIRM 필요."

    existing = load_pending(settings)
    if existing:
        return (
            f"이미 대기 중: {existing.get('code')} ({existing.get('kind')})\n"
            f"/리밸런스승인 {existing.get('code')} 또는 /리밸런스취소"
        )

    snap = snapshot_equity(settings)
    target = settings.rebalance_target
    band = settings.rebalance_band
    share = snap.upbit_share
    lo, hi = target - band, target + band
    direction, move_krw = _plan_move_krw(snap, target=target)

    header = format_snapshot(snap, target=target, band=band)
    if direction == "none" or move_krw < settings.rebalance_min_move_krw:
        return header + f"\n이동 제안 없음 (최소 {settings.rebalance_min_move_krw:,.0f}원)."

    out_of_band = not (lo <= share <= hi)
    if not force and not out_of_band:
        return header + "\n밴드 안 — 강제 제안은 /리밸런스"

    if not force and out_of_band and not _alert_cooldown_ok(settings):
        return header + "\n이탈이지만 알림 쿨다운 중 (다시 보려면 /리밸런스)."

    code = secrets.token_hex(3).upper()
    arrow = "Upbit → Bitget" if direction == "upbit_to_bitget" else "Bitget → Upbit"
    payload = {
        "status": "pending",
        "kind": "rebalance",
        "code": code,
        "direction": direction,
        "move_krw": round(move_krw, 0),
        "created_at": time.time(),
        "reason": reason,
        "snapshot": {
            "upbit_krw": snap.upbit_krw,
            "bitget_krw": snap.bitget_krw,
            "upbit_share": share,
        },
    }
    save_pending(settings, payload)
    if out_of_band:
        _mark_alert_cooldown(settings)

    return "\n".join(
        [
            header,
            "",
            "======= 리밸런스 제안 (미실행) =======",
            f"코드: {code}",
            f"방향: {arrow}",
            f"이동 ≈ {move_krw:,.0f}원 (TRX 브릿지)",
            f"사유: {reason}",
            "",
            f"실행: /리밸런스승인 {code}",
            "취소: /리밸런스취소",
            "====================================",
        ]
    )


def propose_krw_prepare(settings: Settings, target_krw: float) -> str:
    if target_krw <= 0:
        return "금액은 0보다 커야 합니다. 예: /원화준비 500000"
    if not settings.transfer_allowed:
        return "이체 OFF — TRANSFER_ENABLED + TRANSFER_CONFIRM 필요."

    existing = load_pending(settings)
    if existing:
        return (
            f"이미 대기 중: {existing.get('code')} ({existing.get('kind')})\n"
            f"/리밸런스승인 {existing.get('code')} 또는 /리밸런스취소"
        )

    snap = snapshot_equity(settings)
    # Current Upbit KRW cash only (not coins)
    from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

    if not settings.upbit_access_key or not settings.upbit_secret_key:
        return "UPBIT 키 없음"
    client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
    try:
        have_krw = client.available_balance("KRW")
        have_trx = client.available_balance("TRX")
        have_usdt = client.available_balance("USDT")
    finally:
        client.close()

    local_liquid = have_krw + have_trx * snap.trx_krw_px + have_usdt * snap.usdt_krw_px
    need = max(0.0, target_krw - have_krw)
    # Prefer sell local bridge coins first; then pull from Bitget
    sell_local_krw = min(need, local_liquid - have_krw)
    pull_krw = max(0.0, need - max(0.0, sell_local_krw))

    if need <= 0:
        return (
            f"이미 Upbit KRW {have_krw:,.0f}원 ≥ 목표 {target_krw:,.0f}원.\n"
            "추가 이체 불필요."
        )

    code = secrets.token_hex(3).upper()
    payload = {
        "status": "pending",
        "kind": "krw_prepare",
        "code": code,
        "direction": "bitget_to_upbit" if pull_krw > 0 else "local_only",
        "target_krw": target_krw,
        "need_krw": round(need, 0),
        "pull_krw": round(pull_krw, 0),
        "sell_local": True,
        "created_at": time.time(),
        "reason": "krw_prepare",
    }
    save_pending(settings, payload)
    lines = [
        "======= 원화 준비 제안 (미실행) =======",
        f"코드: {code}",
        f"목표 KRW: {target_krw:,.0f}원",
        f"현재 KRW: {have_krw:,.0f}원",
        f"부족: {need:,.0f}원",
        f"Upbit TRX/USDT 매도 활용: {sell_local_krw:,.0f}원분",
        f"Bitget→Upbit TRX 브릿지: {pull_krw:,.0f}원분",
        "",
        f"실행: /리밸런스승인 {code}",
        "취소: /리밸런스취소",
        "====================================",
    ]
    return "\n".join(lines)


def cancel_pending(settings: Settings) -> str:
    req = load_pending(settings)
    if not req:
        return "대기 중인 리밸런스/원화준비가 없습니다."
    save_pending(settings, None)
    return f"취소됨: {req.get('code')} ({req.get('kind')})"


def approve_pending(settings: Settings, code: str) -> str:
    if not settings.transfer_allowed:
        return "이체 설정이 꺼져 있거나 CONFIRM 문구가 맞지 않습니다."
    req = load_pending(settings)
    if not req:
        return "대기 중인 제안이 없습니다."
    if str(req.get("code", "")).upper() != code.strip().upper():
        return "승인 코드가 일치하지 않습니다."

    kind = str(req.get("kind") or "")
    try:
        if kind == "rebalance":
            detail = _execute_rebalance(settings, req)
        elif kind == "krw_prepare":
            detail = _execute_krw_prepare(settings, req)
        else:
            return f"알 수 없는 제안 종류: {kind}"
        save_pending(settings, None)
        return f"실행 완료 ({req.get('code')})\n{detail}"
    except Exception as e:
        logger.exception("rebalance/krw_prepare execute failed")
        return f"실행 실패: {type(e).__name__}: {e}"


def _execute_rebalance(settings: Settings, req: dict[str, Any]) -> str:
    direction = str(req["direction"])
    move_krw = float(req["move_krw"])
    if move_krw < settings.rebalance_min_move_krw:
        raise RuntimeError("이동액이 최소 한도 미만")

    if direction == "upbit_to_bitget":
        amount, px = xfer.plan_trx_withdraw_amount(
            top_up_krw=move_krw,
            transfer_max=settings.transfer_max_amount,
        )
        detail = xfer.auto_fund_bitget_from_upbit(
            settings,
            amount=amount,
            coin="TRX",
            chain="TRX",
            buy_from_krw=True,
            reason="rebalance_u2b",
        )
        return f"Upbit→Bitget ~{move_krw:,.0f}원 ({amount} TRX @ {px:.2f})\n{detail}\n입금 후 Bitget에서 TRX→USDT 환전은 봇 펀딩 대기 또는 /자산 확인."

    if direction == "bitget_to_upbit":
        detail = xfer.auto_fund_upbit_from_bitget(
            settings,
            top_up_krw=move_krw,
            reason="rebalance_b2u",
        )
        return f"Bitget→Upbit ~{move_krw:,.0f}원\n{detail}"

    raise RuntimeError(f"unknown direction {direction}")


def _execute_krw_prepare(settings: Settings, req: dict[str, Any]) -> str:
    target = float(req["target_krw"])
    pull = float(req.get("pull_krw") or 0)
    notes: list[str] = []
    # 1) Sell local TRX/USDT first (no on-chain wait).
    notes.append(xfer.ensure_upbit_krw(settings, target_krw=target, sell_bridge=True))
    # 2) If still short, bridge Bitget→Upbit; deposit is async — user re-runs /원화준비.
    if pull > 0:
        from bot.upbit_client import UpbitPrivate  # noqa: PLC0415

        client = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
        try:
            have = client.available_balance("KRW")
        finally:
            client.close()
        if have + 1e-6 < target:
            still = target - have
            notes.append(
                xfer.auto_fund_upbit_from_bitget(
                    settings,
                    top_up_krw=max(pull, still),
                    reason="krw_prepare",
                )
            )
            notes.append(
                "온체인 입금 대기 후 다시 /원화준비 <목표> 로 KRW 매도를 완료하세요."
            )
    return "\n".join(notes)


def maybe_alert_rebalance(settings: Settings) -> str | None:
    """Call from Upbit bot tick: if out of band and cooldown OK, return alert text."""
    if not settings.rebalance_enabled or settings.paper:
        return None
    if not settings.transfer_allowed:
        return None
    if load_pending(settings):
        return None
    if not _alert_cooldown_ok(settings):
        return None

    snap = snapshot_equity(settings)
    target = settings.rebalance_target
    band = settings.rebalance_band
    share = snap.upbit_share
    if (target - band) <= share <= (target + band):
        return None
    direction, move_krw = _plan_move_krw(snap, target=target)
    if direction == "none" or move_krw < settings.rebalance_min_move_krw:
        return None

    # Create proposal + alert
    return propose_rebalance(settings, force=False, reason="auto_band_breach")
