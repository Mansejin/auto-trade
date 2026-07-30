# Bear short SCALP — Div+ATR v13 (2026-07-30)

Venue: Bitget `BTC/USDT:USDT` isolated futures, Freqtrade, fee **0.06%**.  
CORE / Policy C: **unchanged**. SCALP sleeve research only.

## Hypothesis

Mirror Upbit `daytrade-edge-10m-div-atr-v1` as a **short**:
15m classic/hidden bearish RSI divergence @ BB upper + ATR rising, gated by 1h EMA50&lt;EMA200 → exit BB lower / ROI+2.5% / SL−0.8%.

## Falsify bar (same as v1–v12)

≥2/3 windows: PF&lt;1 or return&lt;0 or WR&lt;38%, or any MDD&gt;10%.

Windows: `20251117-20251228`, `20260121-20260304`, `20260528-20260714`.

## Results

| Window | Market | Trades | Return | PF | MDD | Pass? |
|--------|--------|-------:|-------:|---:|-----:|-------|
| W1 | −6.8% | 7 | **−5.12%** | **0.04** | 5.1% | **FAIL** |
| W2 | −23.0% | 8 | **−0.33%** | **0.93** | 2.7% | **FAIL** |
| W3 | −16.1% | 2 | +0.78% | 1.86 | 0.9% | weak / sparse |

**Verdict: FALSIFIED** (2/3 fail). Do not promote. SCALP bear slot stays cash.

## Reading

Even with BTC dumping 7–23%, selective div shorts still bled on fees/SL (W1 PF≈0).  
Long MR edge does **not** automatically transfer as a short mirror on futures.

## Files

- `freqtrade-research/user_data/strategies/BearShortDivAtrV13.py`
- `freqtrade-research/user_data/config.bitget-bear-div-atr-v13.json`
