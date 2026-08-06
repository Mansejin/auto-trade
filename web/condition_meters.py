"""Map strategy buy/sell conditions onto live indicator values for desk gauges."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_STRAT = Path(os.getenv("STRATEGY_DIR", "/app/strategies"))
if not _STRAT.is_dir():
    _STRAT = Path(__file__).resolve().parent.parent / "strategies"

_REF_LABEL = {
    "ma_short.value": "단기 이평",
    "ma_long.value": "장기 이평",
    "ma_short": "단기 이평",
    "ma_long": "장기 이평",
    "adx14.adx": "ADX",
    "adx14.adx_pdi": "+DI",
    "adx14.adx_mdi": "-DI",
    "rsi14.rsi": "RSI",
    "rsi14.rsi_signal": "RSI시그널",
}

_OP_SYM = {
    "gt": ">",
    "gte": "≥",
    "lt": "<",
    "lte": "≤",
    "eq": "=",
    "cross_above": "↑교차",
    "cross_below": "↓교차",
}


def _basename(path_or_name: Any) -> str | None:
    if path_or_name is None:
        return None
    s = str(path_or_name).strip()
    if not s:
        return None
    return Path(s).name


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ref_label(ref: str) -> str:
    if ref in _REF_LABEL:
        return _REF_LABEL[ref]
    if ref.endswith(".value"):
        return ref_label(ref[: -len(".value")])
    if "." in ref:
        return ref.split(".", 1)[1].replace("_", " ").upper()
    return ref


def lookup_value(values: dict[str, Any], ref: str) -> float | None:
    if not ref:
        return None
    if ref in values:
        try:
            return float(values[ref])
        except (TypeError, ValueError):
            return None
    alt = f"{ref}.value" if "." not in ref else ref[: -len(".value")] if ref.endswith(".value") else None
    if alt and alt in values:
        try:
            return float(values[alt])
        except (TypeError, ValueError):
            return None
    return None


def meter_scale(ref: str, value: float, threshold: float) -> tuple[float, float]:
    key = ref.lower()
    if "rsi" in key or "stoch" in key or "mfi" in key or "cci" in key:
        return 0.0, 100.0
    if "adx" in key or key.endswith("_pdi") or key.endswith("_mdi") or "+di" in key or "-di" in key:
        return 0.0, 60.0
    if "williams" in key or key.endswith(".wr") or "willr" in key:
        return -100.0, 0.0
    lo = min(value, threshold)
    hi = max(value, threshold)
    pad = max(abs(hi - lo) * 0.35, abs(hi) * 0.02, 1.0)
    return lo - pad, hi + pad


def cond_met(op: str, left: float, right: float) -> bool | None:
    if op in ("gt", "cross_above"):
        return left > right
    if op == "gte":
        return left >= right
    if op in ("lt", "cross_below"):
        return left < right
    if op == "lte":
        return left <= right
    if op == "eq":
        return abs(left - right) <= max(1e-9, abs(right) * 1e-9)
    return None


def _walk_rule_leaves(node: Any, side: str, out: list[tuple[str, dict[str, Any]]]) -> None:
    if not isinstance(node, dict):
        return
    kids = node.get("conditions")
    if isinstance(kids, list):
        for child in kids:
            _walk_rule_leaves(child, side, out)
        return
    if node.get("left") and node.get("op"):
        out.append((side, node))


def build_condition_meters(status: dict[str, Any], *, limit: int = 8) -> list[dict[str, Any]]:
    """Map strategy buy/sell thresholds onto current indicator values for desk gauges."""
    values = status.get("values")
    if not isinstance(values, dict) or not values:
        return []
    fname = _basename(status.get("strategy_file")) or _basename(status.get("strategy_path"))
    if not fname:
        return []
    strat = _load_json(_STRAT / fname)
    if not strat:
        return []

    leaves: list[tuple[str, dict[str, Any]]] = []
    _walk_rule_leaves(strat.get("buy"), "buy", leaves)
    _walk_rule_leaves(strat.get("sell"), "sell", leaves)

    meters: list[dict[str, Any]] = []
    seen: set[str] = set()
    for side, leaf in leaves:
        if len(meters) >= limit:
            break
        op = str(leaf.get("op") or "")
        left = leaf.get("left") or {}
        right = leaf.get("right") or {}
        if not isinstance(left, dict) or not isinstance(right, dict):
            continue

        if left.get("type") == "indicator" and right.get("type") == "literal":
            ref = str(left.get("ref") or "")
            cur = lookup_value(values, ref)
            try:
                thr = float(right.get("value"))
            except (TypeError, ValueError):
                continue
            if cur is None or not ref:
                continue
            key = f"{side}:{ref}:{op}:{thr}"
            if key in seen:
                continue
            seen.add(key)
            lo, hi = meter_scale(ref, cur, thr)
            met = cond_met(op, cur, thr)
            meters.append(
                {
                    "kind": "threshold",
                    "side": side,
                    "side_label": "매수" if side == "buy" else "매도",
                    "label": ref_label(ref),
                    "op": op,
                    "op_sym": _OP_SYM.get(op, op),
                    "value": round(cur, 4),
                    "threshold": thr,
                    "min": round(lo, 4),
                    "max": round(hi, 4),
                    "met": met,
                }
            )
            continue

        if left.get("type") == "indicator" and right.get("type") == "indicator":
            lref = str(left.get("ref") or "")
            rref = str(right.get("ref") or "")
            lv = lookup_value(values, lref)
            rv = lookup_value(values, rref)
            if lv is None or rv is None:
                continue
            key = f"{side}:{lref}:{op}:{rref}"
            if key in seen:
                continue
            seen.add(key)
            met = cond_met(op, lv, rv)
            span = abs(lv - rv)
            lo = min(lv, rv) - max(span * 0.25, abs(max(lv, rv)) * 0.01, 1.0)
            hi = max(lv, rv) + max(span * 0.25, abs(max(lv, rv)) * 0.01, 1.0)
            meters.append(
                {
                    "kind": "compare",
                    "side": side,
                    "side_label": "매수" if side == "buy" else "매도",
                    "label": f"{ref_label(lref)} vs {ref_label(rref)}",
                    "op": op,
                    "op_sym": _OP_SYM.get(op, op),
                    "left_label": ref_label(lref),
                    "right_label": ref_label(rref),
                    "left": round(lv, 4),
                    "right": round(rv, 4),
                    "value": round(lv, 4),
                    "threshold": round(rv, 4),
                    "min": round(lo, 4),
                    "max": round(hi, 4),
                    "met": met,
                }
            )
    return meters


_bg_cache: tuple[float, list[list[float]]] | None = None


def _fetch_bitget_5m(symbol: str = "BTCUSDT", limit: int = 120) -> list[list[float]]:
    """Return [ts_ms, o, h, l, c] oldest→newest. Public Bitget mix candles."""
    global _bg_cache
    now = time.time()
    if _bg_cache and now - _bg_cache[0] < 30:
        return _bg_cache[1]
    q = urllib.parse.urlencode(
        {
            "symbol": symbol,
            "productType": "USDT-FUTURES",
            "granularity": "5m",
            "limit": str(limit),
        }
    )
    url = f"https://api.bitget.com/api/v2/mix/market/candles?{q}"
    try:
        with urllib.request.urlopen(url, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return _bg_cache[1] if _bg_cache else []
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        return _bg_cache[1] if _bg_cache else []
    out: list[list[float]] = []
    for r in rows:
        if not isinstance(r, (list, tuple)) or len(r) < 5:
            continue
        try:
            out.append([float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])])
        except (TypeError, ValueError):
            continue
    out.sort(key=lambda x: x[0])
    if out:
        _bg_cache = (now, out)
    return out


def _rma(vals: list[float], period: int) -> list[float | None]:
    """Wilder RMA; None until first seed."""
    out: list[float | None] = [None] * len(vals)
    if period <= 0 or len(vals) < period:
        return out
    seed = sum(vals[:period]) / period
    out[period - 1] = seed
    alpha = 1.0 / period
    prev = seed
    for i in range(period, len(vals)):
        prev = prev + alpha * (vals[i] - prev)
        out[i] = prev
    return out


def _roll_max(xs: list[float], win: int) -> list[float | None]:
    out: list[float | None] = [None] * len(xs)
    for i in range(win - 1, len(xs)):
        out[i] = max(xs[i - win + 1 : i + 1])
    return out


def _roll_min(xs: list[float], win: int) -> list[float | None]:
    out: list[float | None] = [None] * len(xs)
    for i in range(win - 1, len(xs)):
        out[i] = min(xs[i - win + 1 : i + 1])
    return out


def trend_short_snapshot(
    high: list[float], low: list[float], close: list[float], *, period: int = 14
) -> dict[str, float] | None:
    """Last-bar ADX/+DI/-DI + ichimoku cloud spans (TrendShortV1 di_cloud)."""
    n = len(close)
    if n < 80 or len(high) != n or len(low) != n:
        return None
    tr: list[float] = [0.0] * n
    pdm: list[float] = [0.0] * n
    mdm: list[float] = [0.0] * n
    for i in range(1, n):
        up = high[i] - high[i - 1]
        down = low[i - 1] - low[i]
        pdm[i] = up if up > down and up > 0 else 0.0
        mdm[i] = down if down > up and down > 0 else 0.0
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
    atr_f = _rma(tr, period)
    pdm_f = _rma(pdm, period)
    mdm_f = _rma(mdm, period)
    plus_di = [None] * n
    minus_di = [None] * n
    dx = [0.0] * n
    for i in range(n):
        a, p, m = atr_f[i], pdm_f[i], mdm_f[i]
        if a is None or p is None or m is None or a == 0:
            continue
        pdi = 100.0 * p / a
        mdi = 100.0 * m / a
        plus_di[i] = pdi
        minus_di[i] = mdi
        s = pdi + mdi
        dx[i] = 0.0 if s == 0 else abs(pdi - mdi) / s * 100.0
    # ADX = RMA of DX but only after DI is valid; seed from first full DX window.
    first = next((i for i, v in enumerate(plus_di) if v is not None), None)
    if first is None or first + period > n:
        return None
    dx_series = [dx[i] if plus_di[i] is not None else 0.0 for i in range(n)]
    # Seed ADX at first+period-1 using mean of DX over that window of valid bars.
    adx_out: list[float | None] = [None] * n
    start = first + period - 1
    if start >= n:
        return None
    seed = sum(dx_series[first : start + 1]) / period
    adx_out[start] = seed
    prev = seed
    for i in range(start + 1, n):
        prev = (prev * (period - 1) + dx_series[i]) / period
        adx_out[i] = prev

    hh9, ll9 = _roll_max(high, 9), _roll_min(low, 9)
    hh26, ll26 = _roll_max(high, 26), _roll_min(low, 26)
    hh52, ll52 = _roll_max(high, 52), _roll_min(low, 52)
    tenkan = [
        (hh9[i] + ll9[i]) / 2.0 if hh9[i] is not None and ll9[i] is not None else None
        for i in range(n)
    ]
    kijun = [
        (hh26[i] + ll26[i]) / 2.0 if hh26[i] is not None and ll26[i] is not None else None
        for i in range(n)
    ]
    span1 = [
        (tenkan[i] + kijun[i]) / 2.0
        if tenkan[i] is not None and kijun[i] is not None
        else None
        for i in range(n)
    ]
    span2 = [
        (hh52[i] + ll52[i]) / 2.0 if hh52[i] is not None and ll52[i] is not None else None
        for i in range(n)
    ]
    cloud1 = [span1[i - 26] if i >= 26 and span1[i - 26] is not None else None for i in range(n)]
    cloud2 = [span2[i - 26] if i >= 26 and span2[i - 26] is not None else None for i in range(n)]

    i = n - 1
    if (
        adx_out[i] is None
        or plus_di[i] is None
        or minus_di[i] is None
        or cloud1[i] is None
        or cloud2[i] is None
    ):
        return None
    return {
        "close": float(close[i]),
        "adx": float(adx_out[i]),
        "plus_di": float(plus_di[i]),
        "minus_di": float(minus_di[i]),
        "cloud1": float(cloud1[i]),
        "cloud2": float(cloud2[i]),
    }


def meters_from_trend_short_snap(
    snap: dict[str, float], *, adx_min: float = 15.0
) -> list[dict[str, Any]]:
    """di_cloud entry gates as desk meters (side=sell → 숏진입)."""
    mdi, pdi = snap["minus_di"], snap["plus_di"]
    adx, close = snap["adx"], snap["close"]
    c1, c2 = snap["cloud1"], snap["cloud2"]
    meters: list[dict[str, Any]] = []

    def _cmp(label: str, left: float, right: float, op: str, left_l: str, right_l: str) -> None:
        met = cond_met(op, left, right)
        span = abs(left - right)
        lo = min(left, right) - max(span * 0.25, abs(max(left, right)) * 0.01, 1.0)
        hi = max(left, right) + max(span * 0.25, abs(max(left, right)) * 0.01, 1.0)
        meters.append(
            {
                "kind": "compare",
                "side": "sell",
                "side_label": "숏진입",
                "label": label,
                "op": op,
                "op_sym": _OP_SYM.get(op, op),
                "left_label": left_l,
                "right_label": right_l,
                "left": round(left, 4),
                "right": round(right, 4),
                "value": round(left, 4),
                "threshold": round(right, 4),
                "min": round(lo, 4),
                "max": round(hi, 4),
                "met": met,
            }
        )

    def _thr(label: str, value: float, thr: float, op: str, ref: str) -> None:
        lo, hi = meter_scale(ref, value, thr)
        meters.append(
            {
                "kind": "threshold",
                "side": "sell",
                "side_label": "숏진입",
                "label": label,
                "op": op,
                "op_sym": _OP_SYM.get(op, op),
                "value": round(value, 4),
                "threshold": thr,
                "min": round(lo, 4),
                "max": round(hi, 4),
                "met": cond_met(op, value, thr),
            }
        )

    _cmp("-DI vs +DI", mdi, pdi, "gt", "-DI", "+DI")
    _thr("ADX", adx, float(adx_min), "gte", "adx14.adx")
    _cmp("종가 vs 구름1", close, c1, "lt", "종가", "구름1")
    _cmp("종가 vs 구름2", close, c2, "lt", "종가", "구름2")
    return meters


def build_trend_short_meters(*, adx_min: float = 15.0, symbol: str = "BTCUSDT") -> list[dict[str, Any]]:
    rows = _fetch_bitget_5m(symbol=symbol, limit=120)
    if len(rows) < 80:
        return []
    high = [r[2] for r in rows]
    low = [r[3] for r in rows]
    close = [r[4] for r in rows]
    snap = trend_short_snapshot(high, low, close)
    if not snap:
        return []
    return meters_from_trend_short_snap(snap, adx_min=adx_min)


# ponytail: ceiling = DIY Wilder ADX may drift slightly vs talib; upgrade if desk vs bot diverge.
assert meters_from_trend_short_snap(
    {
        "close": 64000,
        "adx": 20,
        "plus_di": 10,
        "minus_di": 18,
        "cloud1": 65000,
        "cloud2": 65500,
    },
    adx_min=15,
)[0]["met"] is True
