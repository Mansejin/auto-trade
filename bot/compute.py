from __future__ import annotations

from typing import Any

from bot.indicators import (
    OHLCV,
    Series,
    ema,
    highest,
    lowest,
    moving_average,
    sma,
    true_range,
)
from bot.strategy_loader import IndicatorDef


def compute_indicator(ind: IndicatorDef, ohlcv: OHLCV) -> dict[str, Series]:
    """Return output_key -> series for one indicator definition."""
    p = ind.params
    t = ind.type

    if t == "moving_average":
        ma_type = str(p.get("type", "SMA"))
        period = int(p.get("period", 20))
        return {"value": moving_average(ohlcv.close, ma_type, period)}

    if t == "rsi":
        return _rsi(ohlcv.close, p)

    if t == "macd":
        return _macd(ohlcv.close, p)

    if t == "bollinger_bands":
        return _bollinger(ohlcv.close, p)

    if t == "atr":
        return _atr(ohlcv, p)

    if t == "stochastic_slow":
        return _stoch_slow(ohlcv, p)

    if t == "williams_r":
        return _williams_r(ohlcv, p)

    if t == "adx":
        return _adx(ohlcv, p)

    if t == "obv":
        return _obv(ohlcv, p)

    if t == "cci":
        return _cci(ohlcv, p)

    if t == "stochastic_rsi":
        return _stoch_rsi(ohlcv.close, p)

    if t == "mfi":
        return _mfi(ohlcv, p)

    if t == "disparity":
        return _disparity(ohlcv.close, p)

    if t == "envelopes":
        return _envelopes(ohlcv.close, p)

    if t == "ichimoku_cloud":
        return _ichimoku(ohlcv, p)

    raise ValueError(f"unsupported indicator type: {t}")


def compute_all(indicators: list[IndicatorDef], ohlcv: OHLCV) -> dict[str, Series]:
    """Flat map of 'ref.output_key' -> series, plus OHLCV fields."""
    out: dict[str, Series] = {
        "open": list(ohlcv.open),
        "high": list(ohlcv.high),
        "low": list(ohlcv.low),
        "close": list(ohlcv.close),
        "volume": list(ohlcv.volume),
    }
    for ind in indicators:
        for key, series in compute_indicator(ind, ohlcv).items():
            out[f"{ind.ref}.{key}"] = series
            # Convenience: moving_average also addressable as ref alone historically
            if key == "value":
                out[ind.ref] = series
    return out


def _rsi(close: list[float], p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 14))
    signal_period = int(p.get("signal_period", 9))
    signal_type = str(p.get("signal_type", "EMA"))
    n = len(close)
    rsi: Series = [None] * n
    if n <= period:
        return {"rsi": rsi, "rsi_signal": [None] * n}

    gains = [0.0]
    losses = [0.0]
    for i in range(1, n):
        delta = close[i] - close[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    rsi[period] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rsi[i] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))

    rsi_vals = [0.0 if v is None else v for v in rsi]
    # signal only where RSI exists
    signal_raw = moving_average(rsi_vals, signal_type, signal_period)
    signal: Series = [None] * n
    for i in range(n):
        if rsi[i] is None or signal_raw[i] is None:
            continue
        # Ensure signal window only uses defined RSI
        if i < period + signal_period - 1:
            continue
        signal[i] = signal_raw[i]
    return {"rsi": rsi, "rsi_signal": signal}


def _macd(close: list[float], p: dict[str, Any]) -> dict[str, Series]:
    fast = int(p.get("fast", 12))
    slow = int(p.get("slow", 26))
    signal_period = int(p.get("signal_period", 9))
    if fast >= slow:
        raise ValueError("macd fast must be < slow")
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    n = len(close)
    macd_line: Series = [None] * n
    for i in range(n):
        if ema_fast[i] is None or ema_slow[i] is None:
            continue
        macd_line[i] = ema_fast[i] - ema_slow[i]  # type: ignore[operator]

    filled = [0.0 if v is None else v for v in macd_line]
    signal_raw = ema(filled, signal_period)
    signal: Series = [None] * n
    hist: Series = [None] * n
    first = slow - 1
    for i in range(n):
        if macd_line[i] is None:
            continue
        if i < first + signal_period - 1:
            continue
        signal[i] = signal_raw[i]
        if signal[i] is not None:
            hist[i] = macd_line[i] - signal[i]  # type: ignore[operator]
    return {"macd": macd_line, "macd_signal": signal, "histogram": hist}


def _bollinger(close: list[float], p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 20))
    mult = float(p.get("multiplier", 2.0))
    mid = sma(close, period)
    n = len(close)
    upper: Series = [None] * n
    lower: Series = [None] * n
    for i in range(period - 1, n):
        if mid[i] is None:
            continue
        window = close[i - period + 1 : i + 1]
        mean = mid[i]
        var = sum((x - mean) ** 2 for x in window) / period  # type: ignore[operator]
        std = var**0.5
        upper[i] = mean + mult * std  # type: ignore[operator]
        lower[i] = mean - mult * std  # type: ignore[operator]
    return {"bb_upper": upper, "bb_middle": mid, "bb_lower": lower}


def _atr(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 14))
    tr = true_range(ohlcv.high, ohlcv.low, ohlcv.close)
    # Wilder smoothing
    n = len(tr)
    atr: Series = [None] * n
    if n < period:
        return {"atr": atr}
    seed = sum(tr[:period]) / period
    atr[period - 1] = seed
    prev = seed
    for i in range(period, n):
        prev = (prev * (period - 1) + tr[i]) / period
        atr[i] = prev
    return {"atr": atr}


def _stoch_slow(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 9))
    k_period = int(p.get("k_period", 3))
    d_period = int(p.get("d_period", 3))
    n = len(ohlcv.close)
    fast_k: Series = [None] * n
    for i in range(period - 1, n):
        hh = highest(ohlcv.high, period, i)
        ll = lowest(ohlcv.low, period, i)
        denom = hh - ll
        fast_k[i] = 0.0 if denom == 0 else (ohlcv.close[i] - ll) / denom * 100.0
    filled_k = [0.0 if v is None else v for v in fast_k]
    slow_k_raw = sma(filled_k, k_period)
    slow_k: Series = [None] * n
    for i in range(n):
        if fast_k[i] is None or i < period - 1 + k_period - 1:
            continue
        slow_k[i] = slow_k_raw[i]
    filled_sk = [0.0 if v is None else v for v in slow_k]
    slow_d_raw = sma(filled_sk, d_period)
    slow_d: Series = [None] * n
    for i in range(n):
        if slow_k[i] is None or i < period - 1 + k_period - 1 + d_period - 1:
            continue
        slow_d[i] = slow_d_raw[i]
    return {"slow_k": slow_k, "slow_d": slow_d}


def _williams_r(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 14))
    n = len(ohlcv.close)
    out: Series = [None] * n
    for i in range(period - 1, n):
        hh = highest(ohlcv.high, period, i)
        ll = lowest(ohlcv.low, period, i)
        denom = hh - ll
        out[i] = 0.0 if denom == 0 else (hh - ohlcv.close[i]) / denom * -100.0
    return {"williams_r": out}


def _adx(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 14))
    n = len(ohlcv.close)
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr = true_range(ohlcv.high, ohlcv.low, ohlcv.close)
    for i in range(1, n):
        up = ohlcv.high[i] - ohlcv.high[i - 1]
        down = ohlcv.low[i - 1] - ohlcv.low[i]
        plus_dm[i] = up if up > down and up > 0 else 0.0
        minus_dm[i] = down if down > up and down > 0 else 0.0

    atr = [None] * n  # type: ignore[var-annotated]
    sm_plus = [None] * n
    sm_minus = [None] * n
    if n <= period:
        return {"adx": [None] * n, "adx_pdi": [None] * n, "adx_mdi": [None] * n}

    atr[period] = sum(tr[1 : period + 1])
    sm_plus[period] = sum(plus_dm[1 : period + 1])
    sm_minus[period] = sum(minus_dm[1 : period + 1])
    for i in range(period + 1, n):
        atr[i] = atr[i - 1] - (atr[i - 1] / period) + tr[i]  # type: ignore[operator,index]
        sm_plus[i] = sm_plus[i - 1] - (sm_plus[i - 1] / period) + plus_dm[i]  # type: ignore[operator,index]
        sm_minus[i] = sm_minus[i - 1] - (sm_minus[i - 1] / period) + minus_dm[i]  # type: ignore[operator,index]

    pdi: Series = [None] * n
    mdi: Series = [None] * n
    dx: Series = [None] * n
    for i in range(period, n):
        if not atr[i]:
            continue
        pdi[i] = 100.0 * sm_plus[i] / atr[i]  # type: ignore[operator,index]
        mdi[i] = 100.0 * sm_minus[i] / atr[i]  # type: ignore[operator,index]
        denom = pdi[i] + mdi[i]  # type: ignore[operator]
        dx[i] = 0.0 if denom == 0 else abs(pdi[i] - mdi[i]) / denom * 100.0  # type: ignore[operator]

    adx: Series = [None] * n
    # First ADX at 2*period
    start = period * 2
    if start < n and all(dx[i] is not None for i in range(period, start)):
        adx[start - 1] = sum(dx[i] for i in range(period, start)) / period  # type: ignore[misc]
        for i in range(start, n):
            if dx[i] is None or adx[i - 1] is None:
                continue
            adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period  # type: ignore[operator]
    return {"adx": adx, "adx_pdi": pdi, "adx_mdi": mdi}


def _obv(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    signal_period = int(p.get("signal_period", 10))
    signal_type = str(p.get("signal_type", "SMA"))
    n = len(ohlcv.close)
    obv = [0.0] * n
    for i in range(1, n):
        if ohlcv.close[i] > ohlcv.close[i - 1]:
            obv[i] = obv[i - 1] + ohlcv.volume[i]
        elif ohlcv.close[i] < ohlcv.close[i - 1]:
            obv[i] = obv[i - 1] - ohlcv.volume[i]
        else:
            obv[i] = obv[i - 1]
    signal = moving_average(obv, signal_type, signal_period)
    return {"obv": list(obv), "obv_signal": signal}


def _cci(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 14))
    signal_period = int(p.get("signal_period", 9))
    signal_type = str(p.get("signal_type", "EMA"))
    n = len(ohlcv.close)
    tp = [(ohlcv.high[i] + ohlcv.low[i] + ohlcv.close[i]) / 3.0 for i in range(n)]
    cci: Series = [None] * n
    for i in range(period - 1, n):
        window = tp[i - period + 1 : i + 1]
        mean = sum(window) / period
        mad = sum(abs(x - mean) for x in window) / period
        cci[i] = 0.0 if mad == 0 else (tp[i] - mean) / (0.015 * mad)
    filled = [0.0 if v is None else v for v in cci]
    signal_raw = moving_average(filled, signal_type, signal_period)
    signal: Series = [None] * n
    for i in range(n):
        if cci[i] is None or i < period - 1 + signal_period - 1:
            continue
        signal[i] = signal_raw[i]
    return {"cci": cci, "cci_signal": signal}


def _stoch_rsi(close: list[float], p: dict[str, Any]) -> dict[str, Series]:
    rsi_period = int(p.get("rsi_period", 14))
    stoch_period = int(p.get("stoch_period", 14))
    k_period = int(p.get("k_period", 3))
    d_period = int(p.get("d_period", 3))
    rsi = _rsi(close, {"period": rsi_period, "signal_period": 1, "signal_type": "SMA"})["rsi"]
    n = len(close)
    raw_k: Series = [None] * n
    for i in range(n):
        if rsi[i] is None:
            continue
        start = i - stoch_period + 1
        if start < 0:
            continue
        window = rsi[start : i + 1]
        if any(v is None for v in window):
            continue
        vals = [float(v) for v in window]  # type: ignore[arg-type]
        lo, hi = min(vals), max(vals)
        raw_k[i] = 0.0 if hi == lo else (float(rsi[i]) - lo) / (hi - lo) * 100.0  # type: ignore[arg-type]
    filled = [0.0 if v is None else v for v in raw_k]
    k_raw = sma(filled, k_period)
    k: Series = [None] * n
    for i in range(n):
        if raw_k[i] is None or i < rsi_period + stoch_period + k_period - 3:
            continue
        k[i] = k_raw[i]
    filled_k = [0.0 if v is None else v for v in k]
    d_raw = sma(filled_k, d_period)
    d: Series = [None] * n
    for i in range(n):
        if k[i] is None or i < rsi_period + stoch_period + k_period + d_period - 4:
            continue
        d[i] = d_raw[i]
    return {"stoch_rsi_k": k, "stoch_rsi_d": d}


def _mfi(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 14))
    n = len(ohlcv.close)
    tp = [(ohlcv.high[i] + ohlcv.low[i] + ohlcv.close[i]) / 3.0 for i in range(n)]
    rmf = [tp[i] * ohlcv.volume[i] for i in range(n)]
    mfi: Series = [None] * n
    for i in range(period, n):
        pos = 0.0
        neg = 0.0
        for j in range(i - period + 1, i + 1):
            if tp[j] > tp[j - 1]:
                pos += rmf[j]
            elif tp[j] < tp[j - 1]:
                neg += rmf[j]
        if neg == 0:
            mfi[i] = 100.0
        else:
            mfi[i] = 100.0 - (100.0 / (1.0 + pos / neg))
    return {"mfi": mfi}


def _disparity(close: list[float], p: dict[str, Any]) -> dict[str, Series]:
    periods = p.get("periods") or [5, 10, 20, 60]
    out: dict[str, Series] = {}
    for period in periods:
        period = int(period)
        ma = sma(close, period)
        series: Series = [None] * len(close)
        for i in range(len(close)):
            if ma[i] is None or ma[i] == 0:
                continue
            series[i] = close[i] / ma[i] * 100.0  # type: ignore[operator]
        out[f"disp_{period}"] = series
    return out


def _envelopes(close: list[float], p: dict[str, Any]) -> dict[str, Series]:
    period = int(p.get("period", 20))
    percent = float(p.get("percent", 6))
    center = sma(close, period)
    n = len(close)
    upper: Series = [None] * n
    lower: Series = [None] * n
    for i in range(n):
        if center[i] is None:
            continue
        upper[i] = center[i] * (1.0 + percent / 100.0)  # type: ignore[operator]
        lower[i] = center[i] * (1.0 - percent / 100.0)  # type: ignore[operator]
    return {"upper": upper, "center": center, "lower": lower}


def _ichimoku(ohlcv: OHLCV, p: dict[str, Any]) -> dict[str, Series]:
    conversion = int(p.get("conversion", 9))
    base = int(p.get("base", 26))
    leading_span2 = int(p.get("leading_span2", 52))
    n = len(ohlcv.close)
    conv: Series = [None] * n
    bas: Series = [None] * n
    lag: Series = [None] * n
    lead1: Series = [None] * n
    lead2: Series = [None] * n
    for i in range(n):
        if i >= conversion - 1:
            conv[i] = (
                highest(ohlcv.high, conversion, i) + lowest(ohlcv.low, conversion, i)
            ) / 2.0
        if i >= base - 1:
            bas[i] = (highest(ohlcv.high, base, i) + lowest(ohlcv.low, base, i)) / 2.0
        lag[i] = ohlcv.close[i]
        if conv[i] is not None and bas[i] is not None:
            lead1[i] = (conv[i] + bas[i]) / 2.0  # type: ignore[operator]
        if i >= leading_span2 - 1:
            lead2[i] = (
                highest(ohlcv.high, leading_span2, i) + lowest(ohlcv.low, leading_span2, i)
            ) / 2.0
    return {
        "Conversion": conv,
        "Base": bas,
        "Lagging": lag,
        "Leading1": lead1,
        "Leading2": lead2,
    }
