"""Pure equity curve helpers for desk (no FastAPI)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable


def equity_summary(
    points: list[dict[str, Any]], *, value_key: str = "equity"
) -> dict[str, Any]:
    if not points:
        return {"n": 0}
    vals: list[float] = []
    for p in points:
        raw = p.get(value_key)
        if raw is None and value_key != "equity":
            raw = p.get("equity")
        if raw is None:
            continue
        vals.append(float(raw))
    if not vals:
        return {"n": 0}
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


def normalize_equity_flows(raw: Any) -> list[dict[str, Any]]:
    """Accept list or {flows:[...]} config; keep withdraw/deposit with amount_krw>0."""
    if isinstance(raw, dict):
        rows = raw.get("flows") or raw.get("items") or []
    elif isinstance(raw, list):
        rows = raw
    else:
        rows = []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind") or row.get("type") or "").strip().lower()
        if kind in ("withdrawal", "out", "cash_out"):
            kind = "withdraw"
        if kind in ("deposit", "in", "cash_in"):
            kind = "deposit"
        if kind not in ("withdraw", "deposit"):
            continue
        try:
            amount = float(row.get("amount_krw") if row.get("amount_krw") is not None else row.get("amount"))
        except (TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        ts = str(row.get("ts") or row.get("date") or "").strip()
        if not ts:
            continue
        out.append(
            {
                "ts": ts,
                "kind": kind,
                "amount_krw": amount,
                "note": str(row.get("note") or "")[:200],
            }
        )
    out.sort(key=lambda r: str(r["ts"]))
    return out


def apply_external_flows(
    points: list[dict[str, Any]],
    flows: list[dict[str, Any]],
    parse_iso_ts: Callable[[str], int | None],
) -> tuple[list[dict[str, Any]], float]:
    """
    Adjust equity for external capital so withdrawals/deposits do not move ret_pct.

    Performance equity = wallet equity + cumulative(withdraw) - cumulative(deposit)
    for all flows with timestamp <= point timestamp.
    """
    if not points:
        return points, 0.0
    parsed_flows: list[tuple[int, str, float]] = []
    for f in flows:
        ts = parse_iso_ts(str(f.get("ts") or ""))
        if ts is None:
            day = str(f.get("ts") or "")[:10]
            if len(day) == 10:
                ts = parse_iso_ts(day + "T00:00:00+09:00")
        if ts is None:
            continue
        parsed_flows.append((ts, str(f["kind"]), float(f["amount_krw"])))
    parsed_flows.sort(key=lambda x: x[0])

    out: list[dict[str, Any]] = []
    net_adjust = 0.0
    for raw in points:
        p = dict(raw)
        wallet = float(p.get("wallet_equity") if p.get("wallet_equity") is not None else p["equity"])
        p["wallet_equity"] = round(wallet, 2)
        raw_ts = str(p.get("ts") or "")
        if len(raw_ts) == 10 and raw_ts[4] == "-" and raw_ts[7] == "-":
            # Date-only marks: treat as end of KST day so same-day flows apply.
            pts = parse_iso_ts(raw_ts + "T23:59:59+09:00")
        else:
            pts = parse_iso_ts(raw_ts)
            if pts is None and len(raw_ts) >= 10:
                pts = parse_iso_ts(raw_ts[:10] + "T23:59:59+09:00")
        adj = 0.0
        if pts is not None:
            for fts, kind, amount in parsed_flows:
                if fts <= pts:
                    adj += amount if kind == "withdraw" else -amount
        net_adjust = adj
        p["equity"] = round(wallet + adj, 2)
        p["flow_adjust_krw"] = round(adj, 2)
        out.append(p)
    return out, round(net_adjust, 2)


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

    flows = [{"ts": "2026-01-02T00:00:00+00:00", "kind": "withdraw", "amount_krw": 100_000}]
    adj_pts, net = apply_external_flows(pts, flows, parse)
    assert net == 100_000
    assert abs(adj_pts[-1]["equity"] - 1_200_000) < 1, adj_pts[-1]
    assert abs(adj_pts[-1]["wallet_equity"] - 1_100_000) < 1
    s2 = equity_summary(adj_pts)
    assert abs(s2["end"] - 1_200_000) < 1
    assert abs(adj_pts[-1]["wallet_equity"] - 1_100_000) < 1
    print("ok", s, s2)


if __name__ == "__main__":
    _demo()
