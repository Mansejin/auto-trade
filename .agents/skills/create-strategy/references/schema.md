# Strategy JSON Schema

Violations raise validation errors.

---

## Full Structure

```json
{
  "name": "Strategy name (non-ASCII allowed)",
  "market": "KRW-BTC",
  "exchange": "kr",
  "timeframe": "1d",
  "stop_loss": 5,
  "take_profit": 15,
  "indicators": [
    { "type": "moving_average", "ref": "ma_short", "params": { "type": "SMA", "period": 5 } },
    { "type": "moving_average", "ref": "ma_long", "params": { "type": "SMA", "period": 20 } }
  ],
  "buy": { "operator": "AND", "conditions": [...] },
  "sell": { "operator": "AND", "conditions": [...] }
}
```

> Do not add descriptive fields outside this structure to strategy JSON. Keep hypotheses, descriptions, and revision reasons separately in user conversation context or the handoff payload.

---

## Field Definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | str | required | Strategy name. Non-ASCII is allowed. |
| `market` | str | required | Upbit market code (for example, `KRW-BTC`). Validated through the Upbit API at runtime. |
| `exchange` | enum | optional | Exchange identifier. Only `kr` (KR exchange) is supported. Defaults to `kr`. |
| `timeframe` | enum | required | One of the 13 values below. **`1y` is not supported.** |
| `indicators` | list | required | Indicator definitions. Duplicate refs are not allowed. |
| `buy` | ConditionGroup | required | Buy condition tree. |
| `sell` | ConditionGroup | required | Sell condition tree. |
| `stop_loss` | float \| null | optional | Percent unit. Null or positive. |
| `take_profit` | float \| null | optional | Percent unit. Null or positive. |

### Allowed timeframe Values

`1M` `1w` `1d` `4h` `1h` `30m` `15m` `10m` `5m` `3m` `1m` `1s`

`1y` is accepted by the schema but has no candle history, so it cannot be backtested. Use `1M` for the longest backtestable trend horizon.

---

## Operands (3 Types)

| type | JSON | Meaning |
|---|---|---|
| `indicator` | `{"type": "indicator", "ref": "ma_short.value"}` | Reference to computed indicator output through `indicator_ref.output_key` dot notation |
| `indicator` + offset | `{"type": "indicator", "ref": "ichi.Leading1", "offset": 26}` | Same as above but shift the series by `offset` bars before comparison. Positive = look back (past bars). Default `0`. Negative values are rejected. |
| `field` | `{"type": "field", "field": "close"}` | OHLCV column: `open` `high` `low` `close` `volume` |
| `field` + offset | `{"type": "field", "field": "close", "offset": 1}` | OHLCV field shifted by `offset` bars. Same sign convention as `indicator` offset. Default `0`. Negative values are rejected. |
| `literal` | `{"type": "literal", "value": 30}` | Constant (float) |

The `ref` of an `indicator` operand must use `{indicators[*].ref}.{output_key}` format. Examples: `rsi14.rsi`, `macd.macd_signal`, `bb20.bb_lower`, `ma20.value`, `ichi.Leading1`.

**`offset` use case — Ichimoku Leading Span:** Leading1 and Leading2 are computed as raw values at the current bar. To compare the current close against the cloud that is _displaced 26 bars into the future_ in a chart, reference the value from 26 bars ago by setting `offset: 26` on the indicator operand:

```json
{ "type": "indicator", "ref": "ichi.Leading1", "offset": 26 }
```

---

## Condition Ops (7 Types)

| op | Meaning | Constraint |
|---|---|---|
| `gt` | left > right | - |
| `lt` | left < right | - |
| `gte` | left >= right | - |
| `lte` | left <= right | - |
| `eq` | left == right | - |
| `cross_above` | left crosses above right | both sides must be time series (literal forbidden) |
| `cross_below` | left crosses below right | both sides must be time series (literal forbidden) |

---

## ConditionGroup (Recursive)

```json
{
  "operator": "AND",
  "conditions": [
    "Condition or ConditionGroup"
  ]
}
```

- `operator`: `"AND"` | `"OR"`
- `conditions`: at least 1 item (empty arrays are rejected). Each element is a leaf `Condition` or nested `ConditionGroup`.

---

## Validation Constraints

Constraints checked by toolkit validation:

1. **Reject types outside the catalog**
   - `indicators[*].type` must be one of the supported catalog's 15 JSON types.
   - Among the 16 selected targets, SMA/EMA are expressed with `moving_average` type and `params.type`, not `sma`/`ema` types.
   - `moving_average.params.type` only allows `SMA` or `EMA`.
   - RSI/CCI/OBV `signal_type` allows `SMA`, `SMMA`, `EMA`, `WMA`, `HMA`.
   - `williams_r` exposes only the normalized output key `williams_r`; `%R` is not a valid strategy ref.
   - `macd.params.fast` must be smaller than `macd.params.slow`.
   - `disparity.params.periods` cannot be an empty array, and each value must be an integer >= 1.
   - Indicator settings must be inside the `params` object. Writing indicator-specific fields such as `period` directly at the indicator top level is rejected.
2. **Reject duplicate refs**
   - The same ref cannot appear twice in one indicators array.
3. **Reject undefined indicator/output references**
   - `IndicatorOperand.ref` in the buy/sell tree must be valid through the full `indicator_ref.output_key`.
   - Example: `ma20` is an invalid reference, and `ma20.value` is valid.
4. **Force time series for cross operators**
   - `LiteralOperand` cannot be used on either side of `cross_above`/`cross_below`.
5. **Reject empty conditions**
   - Groups with `conditions=[]` are rejected.
6. **stop_loss/take_profit positive or null**
   - Values <= 0 are rejected.
7. **Reject top-level fields outside the schema**
   - Do not add descriptive fields such as `description` to strategy JSON.
   - Put strategy descriptions and hypothesis revision reasons in user conversation context or the handoff payload.

Additionally, **market validity** is checked during validation:

8. **market must be in the Upbit supported list** - reject if it is not supported (if the network fails, a `MarketFetchError` is raised — retry after connectivity is restored).

---

## Complex Nested Patterns

### Pattern 1: AND-of-OR - "RSI or Stoch oversold + volume flow recovery"

```json
{
  "operator": "AND",
  "conditions": [
    {
      "operator": "OR",
      "conditions": [
        { "left": { "type": "indicator", "ref": "rsi14.rsi" }, "op": "lt", "right": { "type": "literal", "value": 30 } },
        { "left": { "type": "indicator", "ref": "stoch.slow_k" }, "op": "lt", "right": { "type": "literal", "value": 20 } }
      ]
    },
    {
      "left": { "type": "indicator", "ref": "obv.obv" },
      "op": "gt",
      "right": { "type": "indicator", "ref": "obv.obv_signal" }
    }
  ]
}
```

### Pattern 2: OR-of-AND - "Golden cross OR (above displaced cloud + RSI recovery)"

```json
{
  "operator": "OR",
  "conditions": [
    {
      "left": { "type": "indicator", "ref": "ma_short.value" },
      "op": "cross_above",
      "right": { "type": "indicator", "ref": "ma_long.value" }
    },
    {
      "operator": "AND",
      "conditions": [
        { "left": { "type": "field", "field": "close" }, "op": "gt", "right": { "type": "indicator", "ref": "ichi.Leading1", "offset": 26 } },
        { "left": { "type": "field", "field": "close" }, "op": "gt", "right": { "type": "indicator", "ref": "ichi.Leading2", "offset": 26 } },
        { "left": { "type": "indicator", "ref": "rsi14.rsi" }, "op": "gt", "right": { "type": "literal", "value": 50 } }
      ]
    }
  ]
}
```

### Pattern 3: Below Displaced Ichimoku Cloud

```json
{
  "operator": "AND",
  "conditions": [
    { "left": { "type": "field", "field": "close" }, "op": "lt", "right": { "type": "indicator", "ref": "ichi.Leading1", "offset": 26 } },
    { "left": { "type": "field", "field": "close" }, "op": "lt", "right": { "type": "indicator", "ref": "ichi.Leading2", "offset": 26 } }
  ]
}
```

---

## File Rules

- Path: `{data_root}/strategies/{slug}.json`
- slug: convert `name` to lowercase hyphenated ASCII (for example, "Golden Cross SMA" -> `golden-cross-sma`)
- If the same slug exists, automatically increment to `-v2`, `-v3` (no overwrites)
- When revising a hypothesis after reviewing backtest results (hypothesis -> falsification -> new hypothesis), always save as a new version.
