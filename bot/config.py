from __future__ import annotations

import os
from dataclasses import dataclass, field
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


def _whitelist_from_env(prefix: str) -> dict[str, str]:
    """TRANSFER_WHITELIST_BITGET_USDT=addr → {"USDT": "addr"}."""
    out: dict[str, str] = {}
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
        coin = key[len(prefix) :].strip("_").upper()
        addr = val.strip()
        if coin and addr:
            out[coin] = addr
    return out


@dataclass(frozen=True)
class Settings:
    paper: bool
    exchange: str  # upbit | bitget
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
    bitget_api_key: str
    bitget_secret_key: str
    bitget_passphrase: str
    bitget_category: str
    bitget_product_type: str
    bitget_margin_mode: str
    bitget_margin_coin: str
    bitget_paper_trading: bool
    live_confirm: str
    log_level: str
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_commands: bool
    transfer_enabled: bool
    transfer_confirm: str
    transfer_max_amount: float
    transfer_ttl_sec: int
    transfer_default_chain: str
    transfer_whitelist_bitget: dict[str, str] = field(default_factory=dict)
    transfer_whitelist_upbit: dict[str, str] = field(default_factory=dict)

    @property
    def bitget_ready(self) -> bool:
        return bool(self.bitget_api_key and self.bitget_secret_key and self.bitget_passphrase)

    @property
    def live_allowed(self) -> bool:
        if self.paper or self.live_confirm != "I_UNDERSTAND_LIVE_TRADING_RISK":
            return False
        if self.exchange == "bitget":
            return self.bitget_ready
        return bool(self.upbit_access_key and self.upbit_secret_key)

    @property
    def transfer_allowed(self) -> bool:
        return self.transfer_enabled and self.transfer_confirm == "I_UNDERSTAND_TRANSFER_RISK"

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def telegram_commands_enabled(self) -> bool:
        return self.telegram_enabled and self.telegram_commands

    @property
    def risk_integrity_key(self) -> str:
        """LIVE only: HMAC key for risk.json tamper detection (uses API secret)."""
        if self.paper:
            return ""
        if self.exchange == "bitget":
            return self.bitget_secret_key if self.bitget_secret_key else ""
        if not self.upbit_secret_key:
            return ""
        return self.upbit_secret_key


def load_settings() -> Settings:
    root = Path(os.getenv("BOT_ROOT", "/app"))
    fraction = _env_float("ORDER_FRACTION", 1.0)
    if fraction <= 0 or fraction > 1:
        raise ValueError("ORDER_FRACTION must be in (0, 1]")
    exchange = os.getenv("EXCHANGE", "upbit").strip().lower()
    if exchange not in {"upbit", "bitget"}:
        raise ValueError("EXCHANGE must be 'upbit' or 'bitget'")
    category = (
        os.getenv("BITGET_CATEGORY")
        or os.getenv("BITGET_PRODUCT_TYPE")
        or "USDT-FUTURES"
    ).strip()
    return Settings(
        paper=_env_bool("PAPER", True),
        exchange=exchange,
        strategy_path=Path(
            os.getenv("STRATEGY_PATH", str(root / "strategies" / "sma_cross_btc.json"))
        ),
        state_path=Path(os.getenv("STATE_PATH", str(root / "data" / "state.json"))),
        log_dir=Path(os.getenv("LOG_DIR", str(root / "logs"))),
        poll_seconds=_env_int("POLL_SECONDS", 300),
        paper_cash=_env_float("PAPER_CASH", 1_000_000.0),
        fee_rate=_env_float("FEE_RATE", 0.0005),
        order_fraction=fraction,
        max_order_krw=_env_float("MAX_ORDER_KRW", 0.0),
        max_daily_loss_krw=_env_float("MAX_DAILY_LOSS_KRW", 0.0),
        max_consecutive_errors=_env_int("MAX_CONSECUTIVE_ERRORS", 5),
        upbit_access_key=os.getenv("UPBIT_ACCESS_KEY", "").strip(),
        upbit_secret_key=os.getenv("UPBIT_SECRET_KEY", "").strip(),
        bitget_api_key=os.getenv("BITGET_API_KEY", "").strip(),
        bitget_secret_key=os.getenv("BITGET_SECRET_KEY", "").strip(),
        bitget_passphrase=os.getenv("BITGET_PASSPHRASE", "").strip(),
        bitget_category=category,
        bitget_product_type=category,
        bitget_margin_mode=os.getenv("BITGET_MARGIN_MODE", "isolated").strip().lower(),
        bitget_margin_coin=os.getenv("BITGET_MARGIN_COIN", "USDT").strip().upper(),
        bitget_paper_trading=_env_bool("BITGET_PAPER_TRADING", False),
        live_confirm=os.getenv("LIVE_CONFIRM", "").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        telegram_commands=_env_bool("TELEGRAM_COMMANDS", True),
        transfer_enabled=_env_bool("TRANSFER_ENABLED", False),
        transfer_confirm=os.getenv("TRANSFER_CONFIRM", "").strip(),
        transfer_max_amount=_env_float("TRANSFER_MAX_AMOUNT", 0.0),
        transfer_ttl_sec=_env_int("TRANSFER_TTL_SEC", 600),
        transfer_default_chain=os.getenv("TRANSFER_DEFAULT_CHAIN", "TRC20").strip(),
        transfer_whitelist_bitget=_whitelist_from_env("TRANSFER_WHITELIST_BITGET_"),
        transfer_whitelist_upbit=_whitelist_from_env("TRANSFER_WHITELIST_UPBIT_"),
    )
