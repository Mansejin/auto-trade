# Bear short scalp research — 2026-07-29

Venue: Bitget `BTC/USDT:USDT` isolated futures via Freqtrade (`fee=0.06%` taker).
Upbit spot bot cannot short — Policy C bear (`m5-v6`) **unchanged** (CORE / 장기).
SCALP / 단타 sleeve only — see `config/sleeves.json` (장기70 / 단타30).

Windows (daily-bear calendar): `20251117-20251228`, `20260121-20260304`, `20260528-20260714`.

Falsify if ≥2/3 windows: PF&lt;1 or return&lt;0 or WR&lt;38%, or any window MDD&gt;10%.

## Results

| Ver | Idea | W1 | W2 | W3 | Verdict |
|---|---|---|---|---|---|
| v1 | 5m RSI&gt;70 + BB upper | 0 trades | — | — | dead |
| v2 | 5m RSI×50 below EMA | 56 / 0.71 / −3% | 59 / 0.78 / −3% | 81 / 0.24 / −13% | **falsified** |
| v3 | 15m RSI&gt;58 rally fade | 4 / +0.8% | 1 / +0.07% | 1 / −0.6% | n too small |
| v4–v5 | 1h EMA + RSI pop | PF 0.38–0.81 | … | … | **falsified** |
| v6 | 15m BB breakdown + vol | 18 / 0.86 / −1% | 36 / 0.68 / −5% | 26 / 1.10 / +1% | **falsified** |
| v7 `FailedReclaim` | 15m EMA20 failed reclaim | 44 / 0.74 / −3% | 89 / 0.79 / −6% | 64 / 0.48 / −11% | **falsified** |
| v8 `DiContinuation` | 1h −DI cross | 4 / 0.84 / −0.5% | 8 / 0.10 / −5.5% | 2 / 0 / −1.3% | **falsified** |
| v9 `Donchian` | 15m Donchian + ROI/SL only | 22 / 0.55 / −8% | 44 / 0.83 / −6% | 26 / 1.16 / +3% | **falsified** |
| v10 `4h-gate Donchian` | 4h strong bear + 15m Donchian | 17 / 0.68 / −5% | 26 / 1.15 / +3% | 31 / 0.77 / −6% | **falsified** |
| v11 `4h EMA50 resume` | 4h close×below EMA50 | 0 | 1 / +3.9% | 1 / −2.1% | inconclusive / fail |
| v12 `StochRSI fade` | 1h Stoch×80 in EMA bear | 60 / 0.50 / −19% | 90 / 0.98 / −1% | 58 / 0.92 / −3% | **falsified** |

## Takeaways

1. Fee-aware BTCUSDT short 단타 on these structures does **not** survive 3-window falsification.
2. Occasional single-window wins (v6/v9 W3, v10 W2) are not reproducible — do not promote.
3. CORE bear stays `m5-v6`. SCALP bear slot stays **unfunded (cash)** until a new non-falsified structure appears.
4. Next structures to try later (not retunes): alt perpetual short, funding-crowding fade with full funding history, or multi-asset basket — not more BTC 15m threshold chops.

## Files

- `freqtrade-research/user_data/strategies/BearShort*.py` (v1–v12)
- Configs: `config.bitget-bear-*.json`
