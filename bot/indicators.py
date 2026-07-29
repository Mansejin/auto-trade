from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class OHLCV:
    open: list[float]
    high: list[float]
    low: list[float]
    close: list[float]
    volume: list[float]

    def __len__(self) -> int:
        return len(self.close)

    @classmethod
    def from_upbit_candles(cls, candles: Sequence[dict]) -> OHLCV:
        return cls(
            open=[float(c["opening_price"]) for c in candles],
            high=[float(c["high_price"]) for c in candles],
            low=[float(c["low_price"]) for c in candles],
            close=[float(c["trade_price"]) for c in candles],
            volume=[float(c["candle_acc_trade_volume"]) for c in candles],
        )

    @classmethod
    def from_bitget_candles(cls, rows: Sequence[Sequence[str]]) -> OHLCV:
        # Bitget mix candles: [ts, open, high, low, close, baseVol, quoteVol]
        return cls(
            open=[float(r[1]) for r in rows],
            high=[float(r[2]) for r in rows],
            low=[float(r[3]) for r in rows],
            close=[float(r[4]) for r in rows],
            volume=[float(r[5]) for r in rows],
        )


Series = list[float | None]


def sma(values: Sequence[float], period: int) -> Series:
    if period <= 0:
        raise ValueError("period must be > 0")
    out: Series = [None] * len(values)
    if len(values) < period:
        return out
    window = sum(values[:period])
    out[period - 1] = window / period
    for i in range(period, len(values)):
        window += values[i] - values[i - period]
        out[i] = window / period
    return out


def ema(values: Sequence[float], period: int) -> Series:
    if period <= 0:
        raise ValueError("period must be > 0")
    out: Series = [None] * len(values)
    if len(values) < period:
        return out
    mult = 2.0 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = (values[i] - prev) * mult + prev
        out[i] = prev
    return out


def smma(values: Sequence[float], period: int) -> Series:
    """Smoothed moving average (RMA)."""
    if period <= 0:
        raise ValueError("period must be > 0")
    out: Series = [None] * len(values)
    if len(values) < period:
        return out
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = (prev * (period - 1) + values[i]) / period
        out[i] = prev
    return out


def wma(values: Sequence[float], period: int) -> Series:
    if period <= 0:
        raise ValueError("period must be > 0")
    out: Series = [None] * len(values)
    weights = list(range(1, period + 1))
    denom = period * (period + 1) / 2.0
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        out[i] = sum(v * w for v, w in zip(window, weights)) / denom
    return out


def hma(values: Sequence[float], period: int) -> Series:
    if period <= 0:
        raise ValueError("period must be > 0")
    half = max(1, period // 2)
    sqrt_p = max(1, int(period**0.5))
    wma_half = wma(values, half)
    wma_full = wma(values, period)
    raw: list[float] = []
    # Build compact series for outer WMA; keep alignment via None-aware pass
    diff: Series = [None] * len(values)
    for i in range(len(values)):
        if wma_half[i] is None or wma_full[i] is None:
            continue
        diff[i] = 2.0 * wma_half[i] - wma_full[i]  # type: ignore[operator]
        raw.append(diff[i])  # type: ignore[arg-type]
    # Recompute HMA only on available densified values is awkward; do direct
    out: Series = [None] * len(values)
    # Fill known diff values then WMA over them with None gaps treated carefully
    filled = [0.0 if v is None else v for v in diff]
    # Use rolling WMA only when last sqrt_p diffs are all non-None
    weights = list(range(1, sqrt_p + 1))
    denom = sqrt_p * (sqrt_p + 1) / 2.0
    for i in range(len(values)):
        start = i - sqrt_p + 1
        if start < 0:
            continue
        if any(diff[j] is None for j in range(start, i + 1)):
            continue
        window = filled[start : i + 1]
        out[i] = sum(v * w for v, w in zip(window, weights)) / denom
    return out


def moving_average(values: Sequence[float], ma_type: str, period: int) -> Series:
    kind = ma_type.upper()
    if kind == "SMA":
        return sma(values, period)
    if kind == "EMA":
        return ema(values, period)
    if kind == "SMMA":
        return smma(values, period)
    if kind == "WMA":
        return wma(values, period)
    if kind == "HMA":
        return hma(values, period)
    raise ValueError(f"unsupported MA type: {ma_type}")


def true_range(high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> list[float]:
    out = [high[0] - low[0]]
    for i in range(1, len(close)):
        out.append(
            max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
        )
    return out


def highest(values: Sequence[float], period: int, end: int) -> float:
    start = end - period + 1
    return max(values[start : end + 1])


def lowest(values: Sequence[float], period: int, end: int) -> float:
    start = end - period + 1
    return min(values[start : end + 1])


def last_closed_pair(series: Sequence[float | None]) -> tuple[float | None, float | None]:
    """Closed-bar pair: [-3]=prev, [-2]=curr (exclude forming candle at -1)."""
    if len(series) < 3:
        return None, None
    return series[-3], series[-2]


def closed_value(series: Sequence[float | None], offset: int = 0) -> float | None:
    """Value at closed bar with optional lookback offset (positive = past)."""
    idx = len(series) - 2 - offset
    if idx < 0 or idx >= len(series):
        return None
    return series[idx]


def shift_series(series: Series, offset: int) -> Series:
    """Positive offset looks back: out[i] = series[i - offset]."""
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if offset == 0:
        return list(series)
    out: Series = [None] * len(series)
    for i in range(offset, len(series)):
        out[i] = series[i - offset]
    return out
