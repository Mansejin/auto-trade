# cpp-bt — fast native backtester

OHLCV binary + C++17 sim for multi-symbol JSON strategies and grid search.

## Why

Freqtrade CLI grid (~10s/combo) is too slow for PF scans. This engine loads candles once, computes indicators once, then simulates exit variants in-process.

## Quick start (Windows / MSVC)

```powershell
# 1) export candle bins from FT feathers
.\freqtrade-research\.venv\Scripts\python.exe cpp-bt\tools\export_ohlcv.py --symbol BTC_USDT_USDT --timeframe 5m

# 2) build
powershell -File cpp-bt\scripts\build.ps1

# 3) single run
.\cpp-bt\build\Release\cpp-bt.exe run --strategy cpp-bt\strategies\trend_short_v1.json --data cpp-bt\data --start 2025-09-01 --end 2026-02-04

# 4) grid (wide SL/TP + trailing)
.\cpp-bt\build\Release\cpp-bt.exe grid --grid cpp-bt\grids\trend_short_wide.json --data cpp-bt\data
```

Paths in commands assume cwd = repo root; `grid` resolves `base_strategy` relative to the grid file or repo `cpp-bt/`.

## Strategy JSON

See `strategies/trend_short_v1.json`. Fields: `side`, `symbols[]`, `timeframe`, `fee`, `startup`, `entry.mode` (`cloud_break`|`di_cloud`|`di_only`), `exit.{stoploss,take_profit,trailing,...}`.

## Data export

```powershell
# OHLCV only (legacy)
python cpp-bt/tools/export_ohlcv.py --symbol BTC_USDT_USDT --timeframe 5m
# Preferred: TA-Lib indicators (Freqtrade-aligned entry)
python cpp-bt/tools/export_ftind.py --symbol BTC_USDT_USDT --timeframe 5m
```

`cpp-bt` auto-prefers `data/*.ftind` over `*.ohlcv`.

## Freqtrade cross-check

Use **fixed stake** + `use_order_book: false` when comparing PF. Unlimited compounding changes PF even with the same trades. See `reports/trend-short-cpp-aligned-20260805/NOTES.txt`.
