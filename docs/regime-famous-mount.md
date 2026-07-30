# CORE mount: famous textbook rules

Not GitHub hyperopt bots — authors with decades of published rules.

| Regime | File | Provenance | Toolkit note |
|--------|------|------------|--------------|
| bull / transition | `famous-faber-10mo-sma-1d.json` | Meb Faber GTAA timing | SMA200 (toolkit max period); daily proxy for ~10-mo SMA |
| sideways | `famous-wilder-rsi-mr-1d.json` | J. Welles Wilder RSI | Buy RSI&lt;30 / sell RSI&gt;70 (levels; cross+literal forbidden) |
| bear | `famous-cash-flat-1d.json` | Risk-off cash | Spot can't short; no buys |

SCALP / Bitget: still **OFF**.

Switcher: `scripts/remote_regime_switch.py` → `POLICY`.