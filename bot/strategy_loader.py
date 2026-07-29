from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IndicatorDef:
    type: str
    ref: str
    params: dict[str, Any]


@dataclass(frozen=True)
class Operand:
    kind: str  # indicator | field | literal
    ref: str | None = None
    field: str | None = None
    value: float | None = None
    offset: int = 0


@dataclass(frozen=True)
class Condition:
    left: Operand
    op: str
    right: Operand


@dataclass(frozen=True)
class ConditionGroup:
    operator: str  # AND | OR
    conditions: list[Condition | ConditionGroup]


@dataclass(frozen=True)
class FundingConfig:
    """Auto top-up Bitget UTA from Upbit when a futures entry needs margin."""

    enabled: bool = False
    source: str = "upbit"
    coin: str = "USDT"
    chain: str = "TRC20"
    min_trade_usdt: float = 10.0
    top_up_usdt: float = 50.0
    max_wait_sec: float = 7200.0
    buy_usdt_from_krw: bool = True


@dataclass(frozen=True)
class Strategy:
    name: str
    market: str
    timeframe: str
    stop_loss: float | None
    take_profit: float | None
    indicators: list[IndicatorDef]
    buy: ConditionGroup
    sell: ConditionGroup
    funding: FundingConfig
    raw: dict[str, Any]


def _parse_funding(raw: dict[str, Any] | None) -> FundingConfig:
    if not raw:
        return FundingConfig()
    source = str(raw.get("source") or "upbit").strip().lower()
    if source != "upbit":
        raise ValueError("funding.source currently only supports 'upbit'")
    return FundingConfig(
        enabled=bool(raw.get("enabled")),
        source=source,
        coin=str(raw.get("coin") or "USDT").upper(),
        chain=str(raw.get("chain") or "TRC20").upper(),
        min_trade_usdt=float(raw.get("min_trade_usdt") or 10.0),
        top_up_usdt=float(raw.get("top_up_usdt") or 50.0),
        max_wait_sec=float(raw.get("max_wait_sec") or 7200.0),
        buy_usdt_from_krw=bool(raw.get("buy_usdt_from_krw", True)),
    )


_OP_ALIASES = {
    ">": "gt",
    "<": "lt",
    ">=": "gte",
    "<=": "lte",
    "==": "eq",
}


def _parse_operand(raw: dict[str, Any]) -> Operand:
    kind = str(raw["type"])
    offset = int(raw.get("offset") or 0)
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if kind == "indicator":
        ref = str(raw["ref"])
        return Operand(kind="indicator", ref=ref, offset=offset)
    if kind == "field":
        field = str(raw["field"])
        if field not in {"open", "high", "low", "close", "volume"}:
            raise ValueError(f"unsupported field: {field}")
        return Operand(kind="field", field=field, offset=offset)
    if kind == "literal":
        return Operand(kind="literal", value=float(raw["value"]), offset=0)
    raise ValueError(f"unsupported operand type: {kind}")


def _parse_node(node: dict[str, Any]) -> Condition | ConditionGroup:
    if "operator" in node and "conditions" in node:
        children = node.get("conditions") or []
        if not children:
            raise ValueError("empty conditions group")
        return ConditionGroup(
            operator=str(node["operator"]).upper(),
            conditions=[_parse_node(c) for c in children],
        )
    if "left" in node and "op" in node and "right" in node:
        op = str(node["op"])
        op = _OP_ALIASES.get(op, op)
        return Condition(
            left=_parse_operand(node["left"]),
            op=op,
            right=_parse_operand(node["right"]),
        )
    raise ValueError(f"invalid condition node: {node}")


def _parse_group(raw: dict[str, Any] | None) -> ConditionGroup:
    if not raw:
        return ConditionGroup(operator="AND", conditions=[])
    node = _parse_node(raw)
    if isinstance(node, ConditionGroup):
        return node
    return ConditionGroup(operator="AND", conditions=[node])


def load_strategy(path: Path) -> Strategy:
    raw = json.loads(path.read_text(encoding="utf-8"))
    indicators = [
        IndicatorDef(
            type=str(item["type"]),
            ref=str(item["ref"]),
            params=dict(item.get("params") or {}),
        )
        for item in raw.get("indicators", [])
    ]
    refs = [i.ref for i in indicators]
    if len(refs) != len(set(refs)):
        raise ValueError("duplicate indicator refs")
    return Strategy(
        name=str(raw.get("name") or path.stem),
        market=str(raw["market"]),
        timeframe=str(raw.get("timeframe") or "1d"),
        stop_loss=float(raw["stop_loss"]) if raw.get("stop_loss") is not None else None,
        take_profit=float(raw["take_profit"]) if raw.get("take_profit") is not None else None,
        indicators=indicators,
        buy=_parse_group(raw.get("buy")),
        sell=_parse_group(raw.get("sell")),
        funding=_parse_funding(raw.get("funding") if isinstance(raw.get("funding"), dict) else None),
        raw=raw,
    )
