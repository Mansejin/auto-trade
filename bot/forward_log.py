"""Append-only forward log: one JSON line per closed bar per strategy.

State/signal follow the rule alone (state carried from the previous line), not the
wallet, so the log stays valid when the account is empty or orders are skipped.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bot.indicators import OHLCV
from bot.signals import Signal, evaluate
from bot.strategy_loader import Strategy

logger = logging.getLogger(__name__)


def _last_line(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 4096))
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    return json.loads(lines[-1].decode("utf-8")) if lines else None


def record_forward(
    log_dir: Path,
    slug: str,
    strategy: Strategy,
    ohlcv: OHLCV,
    bar_key: str,
    mode: str,
) -> dict[str, Any] | None:
    """Write one line for bar_key unless it is already the last line. Never raises."""
    try:
        if not bar_key:
            return None
        path = log_dir / "forward" / f"{slug}.jsonl"
        prev = _last_line(path)
        if prev and prev.get("bar") == bar_key:
            return None
        was_in = bool(prev and prev.get("state") == "in_position")
        # ponytail: rule state ignores stop_loss/take_profit (no entry price tracked);
        # add rule entry price to the line if a card ever uses SL/TP.
        result = evaluate(strategy, ohlcv, in_position=was_in, entry_price=None)
        if not result.values:
            return None
        in_pos = result.signal == Signal.BUY or (was_in and result.signal == Signal.HOLD)
        line = {
            "bar": bar_key,
            "close": result.price,
            **{k.removesuffix(".value"): round(v, 4) for k, v in result.values.items()},
            "signal": result.signal.value,
            "state": "in_position" if in_pos else "cash",
            "switched": bool(prev) and in_pos != was_in,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": mode,
            "strategy": strategy.name,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
        logger.info("forward log | %s | %s %s", slug, bar_key, line["state"])
        return line
    except Exception:
        logger.warning("forward log 기록 실패 (주문 로직과 무관)", exc_info=True)
        return None


if __name__ == "__main__":
    import tempfile

    from bot.strategy_loader import load_strategy

    strat = load_strategy(Path(__file__).resolve().parents[1] / "strategies" / "core-btc-sma200-filter-1d.json")

    def bars(*tail: float) -> OHLCV:
        c = [100.0] * 220 + list(tail) + [999.0]  # last = in-progress bar, ignored
        return OHLCV(open=c, high=c, low=c, close=c, volume=[1.0] * len(c))

    with tempfile.TemporaryDirectory() as d:
        log_dir = Path(d)
        a = record_forward(log_dir, "t", strat, bars(200.0), "2026-10-01", "PAPER")
        assert a and a["state"] == "in_position" and a["signal"] == "buy" and not a["switched"], a
        assert a["sma200"] == 100.5 and "sma200.value" not in a, a
        assert record_forward(log_dir, "t", strat, bars(200.0), "2026-10-01", "PAPER") is None
        b = record_forward(log_dir, "t", strat, bars(200.0, 50.0), "2026-10-02", "PAPER")
        assert b and b["state"] == "cash" and b["signal"] == "sell" and b["switched"], b
        c = record_forward(log_dir, "t", strat, bars(200.0, 50.0, 50.0), "2026-10-03", "PAPER")
        assert c and c["state"] == "cash" and c["signal"] == "hold" and not c["switched"], c
        assert record_forward(log_dir, "t", strat, bars(), "", "PAPER") is None
        rows = (log_dir / "forward" / "t.jsonl").read_text(encoding="utf-8").splitlines()
        assert [json.loads(r)["bar"] for r in rows] == ["2026-10-01", "2026-10-02", "2026-10-03"], rows
        print(rows[0])
    print("forward_log self-check OK")
