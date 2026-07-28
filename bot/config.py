from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    paper: bool
    strategy_path: Path
    state_path: Path
    log_dir: Path
    poll_seconds: int
    paper_cash: float
    fee_rate: float
    order_fraction: float
    max_order_krw: float
    max_daily_loss_krw: float
    max_consecutive_errors: int
    upbit_access_key: str
    upbit_secret_key: str
    live_confirm: str
    log_level: str
    telegram_bot_token: str
    telegram_chat_id: str

    @property
    def live_allowed(self) -> bool:
        return (
            not self.paper
            and bool(self.upbit_access_key)
            and bool(self.upbit_secret_key)
            and self.live_confirm == "I_UNDERSTAND_LIVE_TRADING_RISK"
        )

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)


def load_settings() -> Settings:
    root = Path(os.getenv("BOT_ROOT", "/app"))
    fraction = _env_float("ORDER_FRACTION", 1.0)
    if fraction <= 0 or fraction > 1:
        raise ValueError("ORDER_FRACTION must be in (0, 1]")
    return Settings(
        paper=_env_bool("PAPER", True),
        strategy_path=Path(
            os.getenv("STRATEGY_PATH", str(root / "strategies" / "sma_cross_btc.json"))
        ),
        state_path=Path(os.getenv("STATE_PATH", str(root / "data" / "state.json"))),
        log_dir=Path(os.getenv("LOG_DIR", str(root / "logs"))),
        poll_seconds=_env_int("POLL_SECONDS", 300),
        paper_cash=_env_float("PAPER_CASH", 1_000_000.0),
        fee_rate=_env_float("FEE_RATE", 0.0005),
        order_fraction=fraction,
        max_order_krw=_env_float("MAX_ORDER_KRW", 0.0),  # 0 = unlimited
        max_daily_loss_krw=_env_float("MAX_DAILY_LOSS_KRW", 0.0),  # 0 = off
        max_consecutive_errors=_env_int("MAX_CONSECUTIVE_ERRORS", 5),  # 0 = off
        upbit_access_key=os.getenv("UPBIT_ACCESS_KEY", "").strip(),
        upbit_secret_key=os.getenv("UPBIT_SECRET_KEY", "").strip(),
        live_confirm=os.getenv("LIVE_CONFIRM", "").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
    )
