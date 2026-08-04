from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bot.compute import compute_all
from bot.indicators import OHLCV, Series, closed_value, last_closed_pair
from bot.strategy_loader import Condition, ConditionGroup, Operand, Strategy


class Signal(str, Enum):
    HOLD = "hold"
    BUY = "buy"
    SELL = "sell"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


@dataclass(frozen=True)
class EvalResult:
    signal: Signal
    price: float
    values: dict[str, float]
    reason: str


def _cross_above(prev_l: float, curr_l: float, prev_r: float, curr_r: float) -> bool:
    return prev_l <= prev_r and curr_l > curr_r


def _cross_below(prev_l: float, curr_l: float, prev_r: float, curr_r: float) -> bool:
    return prev_l >= prev_r and curr_l < curr_r


def _resolve_series(op: Operand, series_map: dict[str, Series]) -> Series | None:
    if op.kind == "literal":
        return None
    if op.kind == "field":
        key = op.field or ""
    else:
        key = op.ref or ""
        # allow ma_short.value and ma_short
        if key not in series_map and key.endswith(".value"):
            alt = key[: -len(".value")]
            if alt in series_map:
                key = alt
        if key not in series_map and "." not in key and f"{key}.value" in series_map:
            key = f"{key}.value"
    if key not in series_map:
        raise ValueError(f"unknown series ref: {op.ref or op.field}")
    return series_map[key]


def _pair_for_operand(
    op: Operand,
    series_map: dict[str, Series],
) -> tuple[float | None, float | None]:
    if op.kind == "literal":
        assert op.value is not None
        return op.value, op.value
    series = _resolve_series(op, series_map)
    assert series is not None
    # offset shifts the closed-bar window into the past
    if op.offset == 0:
        return last_closed_pair(series)
    # prev at closed-1-offset, curr at closed-offset
    curr = closed_value(series, op.offset)
    prev = closed_value(series, op.offset + 1)
    return prev, curr


def _eval_condition(cond: Condition, series_map: dict[str, Series]) -> bool:
    if cond.op in {"cross_above", "cross_below"}:
        if cond.left.kind == "literal" or cond.right.kind == "literal":
            raise ValueError("cross_* cannot use literal operands")
        prev_l, curr_l = _pair_for_operand(cond.left, series_map)
        prev_r, curr_r = _pair_for_operand(cond.right, series_map)
        if None in (prev_l, curr_l, prev_r, curr_r):
            return False
        assert prev_l is not None and curr_l is not None
        assert prev_r is not None and curr_r is not None
        if cond.op == "cross_above":
            return _cross_above(prev_l, curr_l, prev_r, curr_r)
        return _cross_below(prev_l, curr_l, prev_r, curr_r)

    _, curr_l = _pair_for_operand(cond.left, series_map)
    _, curr_r = _pair_for_operand(cond.right, series_map)
    if curr_l is None or curr_r is None:
        return False

    if cond.op == "gt":
        return curr_l > curr_r
    if cond.op == "lt":
        return curr_l < curr_r
    if cond.op == "gte":
        return curr_l >= curr_r
    if cond.op == "lte":
        return curr_l <= curr_r
    if cond.op == "eq":
        return curr_l == curr_r
    raise ValueError(f"unsupported op: {cond.op}")


def _eval_group(group: ConditionGroup, series_map: dict[str, Series]) -> bool:
    if not group.conditions:
        return False
    results: list[bool] = []
    for node in group.conditions:
        if isinstance(node, ConditionGroup):
            results.append(_eval_group(node, series_map))
        else:
            results.append(_eval_condition(node, series_map))
    if group.operator == "AND":
        return all(results)
    if group.operator == "OR":
        return any(results)
    raise ValueError(f"unsupported group operator: {group.operator}")


def _snapshot_values(series_map: dict[str, Series]) -> dict[str, float]:
    values: dict[str, float] = {}
    for key, series in series_map.items():
        if key in {"open", "high", "low", "close", "volume"}:
            continue
        _, curr = last_closed_pair(series)
        if curr is not None:
            values[key] = curr
    return values


def evaluate(
    strategy: Strategy,
    ohlcv: OHLCV,
    *,
    in_position: bool,
    entry_price: float | None,
) -> EvalResult:
    if len(ohlcv) < 3:
        return EvalResult(Signal.HOLD, 0.0, {}, "insufficient candles")

    price = ohlcv.close[-2]
    series_map = compute_all(strategy.indicators, ohlcv)
    values = _snapshot_values(series_map)

    if in_position and entry_price and entry_price > 0:
        change_pct = (price - entry_price) / entry_price * 100.0
        if strategy.stop_loss is not None and change_pct <= -abs(strategy.stop_loss):
            return EvalResult(
                Signal.STOP_LOSS,
                price,
                values,
                f"stop_loss {change_pct:.2f}% <= -{strategy.stop_loss}%",
            )
        if strategy.take_profit is not None and change_pct >= abs(strategy.take_profit):
            return EvalResult(
                Signal.TAKE_PROFIT,
                price,
                values,
                f"take_profit {change_pct:.2f}% >= {strategy.take_profit}%",
            )

    buy_ok = _eval_group(strategy.buy, series_map)
    sell_ok = _eval_group(strategy.sell, series_map)

    if not in_position and buy_ok:
        return EvalResult(Signal.BUY, price, values, "buy conditions met")
    if in_position and sell_ok:
        return EvalResult(Signal.SELL, price, values, "sell conditions met")
    return EvalResult(Signal.HOLD, price, values, "no signal")
