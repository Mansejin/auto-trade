"""Map strategy buy/sell conditions onto live indicator values for desk gauges."""
from __future__ import annotations

import json
import os
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
