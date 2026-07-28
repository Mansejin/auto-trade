from __future__ import annotations

from datetime import datetime

# Prefer friendly keys; skip duplicate aliases like ma_short vs ma_short.value
_SKIP_SUFFIX_DUP = True

_SIGNAL_KO = {
    "hold": "관망",
    "buy": "매수",
    "sell": "매도",
    "stop_loss": "손절",
    "take_profit": "익절",
}

_REASON_KO = {
    "no signal": "매수/매도 조건 미충족",
    "buy conditions met": "매수 조건 충족",
    "sell conditions met": "매도 조건 충족",
    "insufficient candles": "캔들 데이터 부족",
}

_KEY_LABELS = {
    "ma_short": "단기 이평",
    "ma_short.value": "단기 이평",
    "ma_long": "장기 이평",
    "ma_long.value": "장기 이평",
    "adx14.adx": "ADX(추세강도)",
    "adx14.adx_pdi": "+DI(상승강도)",
    "adx14.adx_mdi": "-DI(하락강도)",
    "rsi14.rsi": "RSI",
    "rsi14.rsi_signal": "RSI 시그널",
    "obv.obv": "OBV",
    "obv.obv_signal": "OBV 시그널",
    "macd.macd": "MACD",
    "macd.macd_signal": "MACD 시그널",
    "macd.histogram": "MACD 히스토그램",
    "bb.bb_upper": "볼린저 상단",
    "bb.bb_middle": "볼린저 중심",
    "bb.bb_lower": "볼린저 하단",
}


def fmt_money(v: float) -> str:
    """KRW display — never show decimals."""
    return f"{int(round(v)):,}"


def fmt_qty(v: float) -> str:
    return f"{v:.8f}".rstrip("0").rstrip(".")


def signal_ko(signal: str) -> str:
    return _SIGNAL_KO.get(signal, signal)


def reason_ko(reason: str) -> str:
    if reason in _REASON_KO:
        return _REASON_KO[reason]
    if reason.startswith("stop_loss"):
        return "손절 조건 도달"
    if reason.startswith("take_profit"):
        return "익절 조건 도달"
    return reason


def mode_ko(mode: str) -> str:
    m = mode.upper()
    if m == "LIVE":
        return "실주문"
    if m == "PAPER":
        return "모의투자"
    return mode


def market_ko(market: str) -> str:
    names = {
        "KRW-BTC": "비트코인",
        "KRW-ETH": "이더리움",
        "KRW-XRP": "리플",
    }
    base = names.get(market)
    return f"{base} ({market})" if base else market


def _label_for_key(key: str) -> str:
    if key in _KEY_LABELS:
        return _KEY_LABELS[key]
    # ma_short.value style
    if key.endswith(".value"):
        root = key[: -len(".value")]
        if root in _KEY_LABELS:
            return _KEY_LABELS[root]
        if root.startswith("ma_"):
            return f"이평({root})"
    if "." in key:
        ref, out = key.split(".", 1)
        out_map = {
            "adx": "ADX",
            "adx_pdi": "+DI",
            "adx_mdi": "-DI",
            "rsi": "RSI",
            "rsi_signal": "RSI 시그널",
            "obv": "OBV",
            "obv_signal": "OBV 시그널",
            "macd": "MACD",
            "macd_signal": "MACD 시그널",
            "histogram": "히스토그램",
            "value": "값",
        }
        nice = out_map.get(out, out)
        return f"{ref} {nice}"
    return key


def _fmt_indicator_value(key: str, value: float) -> str:
    # Oscillators: 1 decimal; prices: integer won
    osc_parts = ("adx", "rsi", "pdi", "mdi", "stoch", "mfi", "williams", "histogram")
    low = key.lower()
    if any(p in low for p in osc_parts):
        return f"{value:.1f}"
    return fmt_money(value)


def format_indicators(values: dict[str, float], limit: int = 8) -> list[str]:
    """Return Korean bullet lines; dedupe alias keys."""
    seen_labels: set[str] = set()
    lines: list[str] = []

    # Prefer *.value / detailed keys over bare aliases
    items = sorted(
        values.items(),
        key=lambda kv: (0 if "." in kv[0] else 1, kv[0]),
    )
    for key, value in items:
        label = _label_for_key(key)
        if label in seen_labels:
            continue
        seen_labels.add(label)
        lines.append(f"· {label}: {_fmt_indicator_value(key, value)}")
        if len(lines) >= limit:
            break
    return lines


def format_status_block(
    *,
    mode: str,
    strategy: str,
    market: str,
    timeframe: str,
    price: float,
    signal: str,
    reason: str,
    krw: float | None,
    base: str,
    base_qty: float | None,
    position: str,
    values: dict[str, float],
) -> str:
    lines = [
        "======= 봇 상태 =======",
        f"시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"모드: {mode_ko(mode)}",
        f"전략: {strategy}",
        f"종목: {market_ko(market)}",
        f"봉간격: {timeframe}",
        f"현재가: {fmt_money(price)}원",
        f"판단: {signal_ko(signal)} — {reason_ko(reason)}",
        f"보유: {position}",
    ]
    if krw is not None:
        lines.append(f"원화 잔고: {fmt_money(krw)}원")
    if base_qty is not None:
        lines.append(f"{base} 잔고: {fmt_qty(base_qty)}")

    ind = format_indicators(values)
    if ind:
        lines.append("")
        lines.append("---- 주요 지표 ----")
        lines.extend(ind)

    lines.append("======================")
    return "\n".join(lines)
