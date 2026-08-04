from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Position:
    market: str
    qty: float
    entry_price: float
    opened_at: str


@dataclass
class Trade:
    ts: str
    side: str
    market: str
    price: float
    qty: float
    fee: float
    reason: str
    paper: bool


@dataclass
class Portfolio:
    cash: float
    position: Position | None = None
    trades: list[Trade] = field(default_factory=list)
    last_signal_bar: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "cash": self.cash,
            "position": asdict(self.position) if self.position else None,
            "trades": [asdict(t) for t in self.trades],
            "last_signal_bar": self.last_signal_bar,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], default_cash: float) -> Portfolio:
        pos_raw = data.get("position")
        position = Position(**pos_raw) if pos_raw else None
        trades = [Trade(**t) for t in data.get("trades", [])]
        return cls(
            cash=float(data.get("cash", default_cash)),
            position=position,
            trades=trades,
            last_signal_bar=data.get("last_signal_bar"),
        )

    @property
    def in_position(self) -> bool:
        return self.position is not None and self.position.qty > 0

    def equity(self, mark_price: float) -> float:
        if not self.position:
            return self.cash
        return self.cash + self.position.qty * mark_price
