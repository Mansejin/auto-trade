from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from bot.integrity import INTEGRITY_FIELD, attach_integrity, restrict_path_mode, verify_dict

logger = logging.getLogger(__name__)


@dataclass
class RiskState:
    day_key: str = ""
    day_start_equity: float = 0.0
    consecutive_errors: int = 0
    trading_halted: bool = False
    halt_reason: str = ""
    halt_buys_only: bool = False

    def to_dict(self) -> dict:
        return {
            "day_key": self.day_key,
            "day_start_equity": self.day_start_equity,
            "consecutive_errors": self.consecutive_errors,
            "trading_halted": self.trading_halted,
            "halt_reason": self.halt_reason,
            "halt_buys_only": self.halt_buys_only,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> RiskState:
        if not data:
            return cls()
        return cls(
            day_key=str(data.get("day_key") or ""),
            day_start_equity=float(data.get("day_start_equity") or 0.0),
            consecutive_errors=int(data.get("consecutive_errors") or 0),
            trading_halted=bool(data.get("trading_halted")),
            halt_reason=str(data.get("halt_reason") or ""),
            halt_buys_only=bool(data.get("halt_buys_only")),
        )


def risk_path(state_path: Path) -> Path:
    return state_path.with_name("risk.json")


def load_risk(state_path: Path, *, integrity_key: str = "") -> RiskState:
    path = risk_path(state_path)
    if not path.exists():
        return RiskState()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        key = integrity_key.strip()
        if key and raw.get(INTEGRITY_FIELD) and not verify_dict(raw, key):
            logger.error("risk.json integrity verification failed — halting trading")
            return RiskState(
                trading_halted=True,
                halt_reason="risk.json integrity check failed (possible tampering)",
            )
        if key and raw and not raw.get(INTEGRITY_FIELD):
            logger.warning("risk.json lacks integrity signature; signing on next save")
        body = {k: v for k, v in raw.items() if k != INTEGRITY_FIELD}
        return RiskState.from_dict(body)
    except Exception:
        logger.exception("risk.json 로드 실패 — 초기화")
        return RiskState()


def save_risk(state_path: Path, risk: RiskState, *, integrity_key: str = "") -> None:
    path = risk_path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = attach_integrity(risk.to_dict(), integrity_key.strip())
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    restrict_path_mode(path)


def today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def refresh_day(risk: RiskState, equity: float) -> RiskState:
    key = today_key()
    if risk.day_key != key:
        risk.day_key = key
        risk.day_start_equity = equity
        # Clear daily-loss halt on new day; keep hard error halt
        if risk.halt_buys_only:
            risk.trading_halted = False
            risk.halt_reason = ""
            risk.halt_buys_only = False
        logger.info("리스크 일일 기준 갱신 | equity=%s", round(equity))
    elif risk.day_start_equity <= 0 and equity > 0:
        risk.day_start_equity = equity
    return risk


def check_daily_loss(risk: RiskState, equity: float, max_daily_loss_krw: float) -> RiskState:
    if max_daily_loss_krw <= 0 or risk.day_start_equity <= 0:
        return risk
    loss = risk.day_start_equity - equity
    if loss >= max_daily_loss_krw:
        risk.trading_halted = True
        risk.halt_buys_only = True
        risk.halt_reason = (
            f"일일 손실 한도 도달 (손실 {int(loss)}원 >= {int(max_daily_loss_krw)}원). "
            "신규 매수 중단. 매도는 허용."
        )
        logger.warning(risk.halt_reason)
    return risk


def record_success(risk: RiskState) -> RiskState:
    risk.consecutive_errors = 0
    return risk


def record_error(risk: RiskState, max_consecutive: int) -> RiskState:
    risk.consecutive_errors += 1
    if max_consecutive > 0 and risk.consecutive_errors >= max_consecutive:
        risk.trading_halted = True
        risk.halt_buys_only = False
        risk.halt_reason = (
            f"연속 오류 {risk.consecutive_errors}회 - 주문 전면 중단. "
            "risk.json 수동 해제 또는 재시작 전 원인 확인."
        )
        logger.error(risk.halt_reason)
    return risk


def allow_buy(risk: RiskState) -> bool:
    return not risk.trading_halted


def allow_sell(risk: RiskState) -> bool:
    if not risk.trading_halted:
        return True
    return risk.halt_buys_only
