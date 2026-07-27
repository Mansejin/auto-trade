# Indicator Catalog (16 Targets)

Only indicators in the supported catalog are available. Types outside the catalog are rejected at validation.

16 target indicators collapse SMA and EMA into one `moving_average` type, leaving 15 JSON type literals. To use SMA or EMA, set `moving_average.params.type` accordingly.

> **Common cautions**
> - All indicators use fixed OHLCV columns (`open`/`high`/`low`/`close`/`volume`). Using schema-unknown fields such as `source` in strategy JSON causes validation errors.
> - Indicator-specific settings must be placed inside the `params` object. Example: `{ "type": "moving_average", "ref": "ma20", "params": { "type": "SMA", "period": 20 } }`.
> - `ref` must be unique within the indicators array. To use the same type twice with different parameters, register two items with different refs such as `ma_short` / `ma_long`.
> - Use `indicator_ref.output_key` dot notation when referencing indicators in conditions. Examples: `ma20.value`, `macd.macd_signal`, `bb.bb_lower`.
> - `moving_average.params.type` only allows `SMA` or `EMA`. If multiple moving averages are needed, split them into multiple declarations with different refs.
> - RSI/OBV/CCI `signal_type` allows `SMA`, `SMMA`, `EMA`, `WMA`, `HMA`.
> - Williams %R uses the normalized output key `williams_r`. Do not use legacy `%R` in strategy JSON refs.
> - No indicator returns bool. Express Ichimoku "above/below cloud" conditions by comparing `close` with `ichi.Leading1`/`ichi.Leading2`.

---

## Supported Types and Output Keys

| type | params (default) | output keys | Cautions |
|---|---|---|---|
| `rsi` | `period=14`, `signal_period=9`, `signal_type="EMA"` | `rsi`, `rsi_signal` | 0-100 range. `signal_type` allows `SMA`, `SMMA`, `EMA`, `WMA`, `HMA`. |
| `macd` | `fast=12`, `slow=26`, `signal_period=9` | `macd`, `macd_signal`, `histogram` | `fast` must be smaller than `slow`. One indicator returns MACD line, signal, and histogram together. |
| `bollinger_bands` | `period=20`, `multiplier=2.0` | `bb_upper`, `bb_middle`, `bb_lower` | Reference upper/middle/lower bands as output keys under one ref. |
| `moving_average` | `type="SMA"`, `period=20` | `value` | `params.type` only allows `SMA` or `EMA`. If multiple MAs are needed, declare multiple refs. |
| `atr` | `period=14` | `atr` | Directionless volatility indicator. Better suited for filters or risk conditions than standalone entry signals. |
| `stochastic_slow` | `period=9`, `k_period=3`, `d_period=3` | `slow_k`, `slow_d` | 0-100 range. K/D crosses compare the two output keys. |
| `williams_r` | `period=14` | `williams_r` | -100 to 0 oscillator. The strategy ref key is normalized to `williams_r`, not `%R`. |
| `adx` | `period=14` | `adx`, `adx_pdi`, `adx_mdi` | `adx` is trend strength; `adx_pdi`/`adx_mdi` are used for directional comparison. |
| `obv` | `signal_period=10`, `signal_type="SMA"` | `obv`, `obv_signal` | Returns cumulative volume and signal line together. `signal_type` allows `SMA`, `SMMA`, `EMA`, `WMA`, `HMA`. |
| `cci` | `period=14`, `signal_period=9`, `signal_type="EMA"` | `cci`, `cci_signal` | Used for zero-line, +100, -100 comparisons and signal crosses. `signal_type` allows `SMA`, `SMMA`, `EMA`, `WMA`, `HMA`. |
| `stochastic_rsi` | `rsi_period=14`, `stoch_period=14`, `k_period=3`, `d_period=3` | `stoch_rsi_k`, `stoch_rsi_d` | 0-100 oscillator applying the stochastic formula to RSI. |
| `mfi` | `period=14` | `mfi` | 0-100 oscillator reflecting volume. |
| `disparity` | `periods=[5,10,20,60]` | `disp_5`, `disp_10`, `disp_20`, `disp_60` | `periods` only allows integers >= 1. Changing it also changes `disp_{period}` output keys. |
| `envelopes` | `period=20`, `percent=6` | `upper`, `center`, `lower` | Fixed-percent bands. Use `upper`/`center`/`lower`, not `bb_*`. |
| `ichimoku_cloud` | `conversion=9`, `base=26`, `leading_span2=52` | `Conversion`, `Base`, `Lagging`, `Leading1`, `Leading2` | Output key casing matters. Cloud conditions compare `Leading1` and `Leading2` separately. |

---

## Common Reference Examples

### Moving Average Golden Cross

```json
"indicators": [
  { "type": "moving_average", "ref": "ma_short", "params": { "type": "SMA", "period": 5 } },
  { "type": "moving_average", "ref": "ma_long", "params": { "type": "SMA", "period": 20 } }
],
"buy": {
  "operator": "AND",
  "conditions": [
    {
      "left": { "type": "indicator", "ref": "ma_short.value" },
      "op": "cross_above",
      "right": { "type": "indicator", "ref": "ma_long.value" }
    }
  ]
}
```

### MACD Signal Cross

```json
{
  "left": { "type": "indicator", "ref": "macd.macd" },
  "op": "cross_above",
  "right": { "type": "indicator", "ref": "macd.macd_signal" }
}
```

### Williams %R Oversold Filter

```json
{
  "left": { "type": "indicator", "ref": "wr.williams_r" },
  "op": "lt",
  "right": { "type": "literal", "value": -80 }
}
```

### Above Ichimoku Cloud

Express price above the cloud as an AND condition where close is greater than both leading spans.

```json
{
  "operator": "AND",
  "conditions": [
    {
      "left": { "type": "field", "field": "close" },
      "op": "gt",
      "right": { "type": "indicator", "ref": "ichi.Leading1" }
    },
    {
      "left": { "type": "field", "field": "close" },
      "op": "gt",
      "right": { "type": "indicator", "ref": "ichi.Leading2" }
    }
  ]
}
```
