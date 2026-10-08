"""Load a strategy JSON, fetch live Upbit candles like the bot does, print the current signal.

Usage: python scripts/check_strategy_signal.py strategies/core-btc-sma200-filter-1d.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot.indicators import OHLCV
from bot.signals import evaluate
from bot.strategy_loader import load_strategy
from bot.upbit_client import UpbitPublic

strategy = load_strategy(Path(sys.argv[1]))
count = int(strategy.raw.get("history_bars") or 200)
candles = UpbitPublic().candles(strategy.market, strategy.timeframe, count=count)
dates = [c["candle_date_time_utc"] for c in candles]
assert len(candles) == count, (len(candles), count)
assert dates == sorted(set(dates)), "candles must be unique and oldest-first"

ohlcv = OHLCV.from_upbit_candles(candles)
for in_pos in (False, True):
    r = evaluate(strategy, ohlcv, in_position=in_pos, entry_price=None)
    print(f"in_position={in_pos}: {r.signal.value} price={r.price} values={r.values} ({r.reason})")
print(f"candles={len(candles)} {dates[0]} .. {dates[-1]}")
