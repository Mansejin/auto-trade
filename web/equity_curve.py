"""Pure equity curve helpers for desk (no FastAPI)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


def equity_summary(points: list[dict[str, Any]]) -> dict[str, Any]:
    if not points:
        return {"n": 0}
    vals = [float(p["equity"]) for p in points]
    start, end = vals[0], vals[-1]
    peak = vals[0]
    mdd = 0.0
    for v in vals:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, (v - peak) / peak)
    ret = ((end / start) - 1.0) * 100.0 if start else 0.0
    return {
        "n": len(vals),
        "start": round(start, 2),
        "end": round(end, 2),
        "ret_pct": round(ret, 2),
        "mdd_pct": round(mdd * 100.0, 2),
        "high": round(max(vals), 2),
        "low": round(min(vals), 2),
    }


def equity_curve_from_trades(
    trades: list[dict[str, Any]],
    daily_closes: list[tuple[int, float]],
    end_cash: float,
    end_qty: float,
    parse_iso_ts: Callable[[str], int | None],
) -> list[dict[str, Any]]:
    """Rebuild approximate Upbit equity path from trades + daily closes."""
    sorted_trades = sorted(
        (t for t in trades if t.get("side") in ("buy", "sell") and t.get("price") and t.get("qty")),
        key=lambda t: str(t.get("ts") or ""),
    )
    cash = float(end_cash)
    qty = float(end_qty)
    for t in reversed(sorted_trades):
        side = str(t["side"]).lower()
        px = float(t["price"])
        q = float(t["qty"])
        fee = float(t.get("fee") or 0)
        if side == "sell":
            cash -= px * q - fee
            qty += q
        else:
            cash += px * q + fee
            qty -= q
    if not daily_closes:
        return []

    trade_events: list[tuple[int, dict[str, Any]]] = []
    for t in sorted_trades:
        ts = parse_iso_ts(str(t.get("ts") or ""))
        if ts is not None:
            trade_events.append((ts, t))

    points: list[dict[str, Any]] = []
    ti = 0

    def _apply(t: dict[str, Any], ts: int) -> None:
        nonlocal cash, qty
        side = str(t["side"]).lower()
        px = float(t["price"])
        q = float(t["qty"])
        fee = float(t.get("fee") or 0)
        if side == "buy":
            cash -= px * q + fee
            qty += q
        else:
            cash += px * q - fee
            qty -= q
        points.append(
            {
                "ts": datetime.fromtimestamp(ts, tz=timezone.utc)
                .astimezone()
                .isoformat(timespec="seconds"),
                "equity": round(cash + qty * px, 2),
                "source": "trade",
                "side": side,
            }
        )

    first_day = daily_closes[0][0]
    while ti < len(trade_events) and trade_events[ti][0] < first_day:
        _apply(trade_events[ti][1], trade_events[ti][0])
        ti += 1

    for day_ts, close in daily_closes:
        while ti < len(trade_events) and trade_events[ti][0] <= day_ts + 86400 - 1:
            _apply(trade_events[ti][1], trade_events[ti][0])
            ti += 1
        points.append(
            {
                "ts": datetime.fromtimestamp(day_ts, tz=timezone.utc)
                .astimezone()
                .isoformat(timespec="seconds")[:10],
                "equity": round(cash + qty * close, 2),
                "source": "mtm",
            }
        )
    while ti < len(trade_events):
        _apply(trade_events[ti][1], trade_events[ti][0])
        ti += 1
    return points


def _demo() -> None:
    def parse(s: str) -> int | None:
        try:
            return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())
        except Exception:
            return None

    # start 1_000_000, buy 0.01 @ 100m (=1m), fee 0 → cash 0, qty 0.01
    # day close 110m → equity 1.1m; sell all → cash 1.1m
    day0 = parse("2026-01-01T00:00:00+00:00")
    day1 = parse("2026-01-02T00:00:00+00:00")
    assert day0 and day1
    trades = [
        {
            "ts": "2026-01-01T12:00:00+00:00",
            "side": "buy",
            "price": 100_000_000,
            "qty": 0.01,
            "fee": 0,
        },
        {
            "ts": "2026-01-02T12:00:00+00:00",
            "side": "sell",
            "price": 110_000_000,
            "qty": 0.01,
            "fee": 0,
        },
    ]
    daily = [(day0, 100_000_000.0), (day1, 110_000_000.0)]
    pts = equity_curve_from_trades(trades, daily, end_cash=1_100_000.0, end_qty=0.0, parse_iso_ts=parse)
    assert pts, pts
    # last point after sell should be ~1.1m
    assert abs(pts[-1]["equity"] - 1_100_000) < 1, pts[-1]
    s = equity_summary(pts)
    assert s["end"] == 1_100_000.0
    print("ok", s)


if __name__ == "__main__":
    _demo()
