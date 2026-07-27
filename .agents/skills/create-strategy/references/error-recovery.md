# Self-Correction Loop (Validation Error -> Patch)

The skill directly diagnoses, patches, and revalidates errors that occur during strategy validation. Do not ask the user.

Loop limit: maximum 3 attempts. When the limit is exceeded, ask the user to renegotiate the hypothesis.

---

## 9 Patch Patterns

### 1. Type Outside the Catalog

**Diagnosis**: an unsupported indicator type is used.

**Patch**: replace with the closest catalog indicator.
- `sma`, `ema` -> `moving_average` + `params.type`
- `bollinger`, `bb_upper`, `bb_lower` -> `bollinger_bands`
- `macd_signal`, `macd_hist` -> output keys of `macd`
- `stoch_k`, `stoch_d` -> `slow_k`/`slow_d` of `stochastic_slow`

---

### 2. Duplicate ref

**Diagnosis**: the same ref is registered two or more times.

**Patch**: add `_2`, `_3` suffixes from the second occurrence onward. Prefer meaningful names (`ma_short`, `ma_long`, `macd_fast`) when possible.

---

### 3. Undefined Indicator Ref

A condition uses a `ref` that does not appear in the `indicators` array (direct ref, no dot notation).

**Diagnosis**: a condition references a ref that is not defined in indicators.

**Patch**: choose one of two options.
- If the intent is correct, add that ref to the indicators array
- If it is a typo, replace it with one of the defined refs

---

### 4. Undefined output key Reference

A condition uses dot notation (`ref.key`) but the output key does not match the indicator spec.

**Diagnosis**: dot notation is used, but the output key does not match the indicator spec.

**Patch**: replace with the exact key based on output keys in [indicators.md](indicators.md).
- `ma_short` -> `ma_short.value`
- `macd.signal` -> `macd.macd_signal`
- `macd.macd_hist` -> `macd.histogram`
- `bb.upper` -> `bb.bb_upper`
- `env.envelope_upper` -> `env.upper`
- `wr.%R` -> `wr.williams_r`
- `ichi.leading1` -> `ichi.Leading1`
- `disp.value` or `disp.disparity_N` -> `disp.disp_{N}` (e.g., `disp.disp_20` for period 20)

---

### 5. literal in a cross Operator

**Diagnosis**: a constant value is used in a cross operator.

**Patch**: change the op according to intent.
- "RSI crosses above 30" -> `cross_above 30` is impossible -> `gt 30`
- "MACD crosses the zero line" -> there is no indicator representing 0, so simplify to `gt 0` / `lt 0`

---

### 6. Single bool Condition for Ichimoku Cloud

**Diagnosis**: above/below Ichimoku cloud was referenced as a single true/false value, or only the ref was used without an output key.

**Patch**: declare `ichimoku_cloud` and express above/below cloud as output-key comparisons.

Above cloud:
```json
{
  "operator": "AND",
  "conditions": [
    { "left": { "type": "field", "field": "close" }, "op": "gt", "right": { "type": "indicator", "ref": "ichi.Leading1" } },
    { "left": { "type": "field", "field": "close" }, "op": "gt", "right": { "type": "indicator", "ref": "ichi.Leading2" } }
  ]
}
```

Below cloud:
```json
{
  "operator": "AND",
  "conditions": [
    { "left": { "type": "field", "field": "close" }, "op": "lt", "right": { "type": "indicator", "ref": "ichi.Leading1" } },
    { "left": { "type": "field", "field": "close" }, "op": "lt", "right": { "type": "indicator", "ref": "ichi.Leading2" } }
  ]
}
```

---

### 7. Empty conditions

**Diagnosis**: the buy or sell condition group is empty.

**Patch**: add at least 1 condition. If the hypothesis has no buy/sell condition, the hypothesis itself is incomplete, so return to STEP 1 and renegotiate.

---

### 8. Invalid market or Risk Value

**Diagnosis**: the market code is invalid or on the wrong exchange; or the market list API is currently unavailable; or stop-loss/take-profit is 0 or below.

**Patch**:
- market errors cannot be self-corrected. Ask the user to confirm the market code.
- If the market list API request fails (`MarketFetchError`), retry after connectivity is restored.
- If `0` was intended, correct to `null` or reasonable defaults (`stop_loss=5`, `take_profit=15`).

---

### 9. Top-Level Field Outside the Schema

**Diagnosis**: a descriptive field not used for strategy execution, or a typo field, is included in strategy JSON.

**Patch**:
- Remove descriptive fields such as `description`, `reason`, `hypothesis_note` from strategy JSON
- Keep hypotheses, descriptions, and revision reasons in user conversation context or the backtest handoff payload
- If it is a typo field, fix it to the official field name in [schema.md](schema.md)

---

## Revalidation Flow

1. Synthesize strategy JSON from the approved four parts.
2. Validate with `bash scripts/upbit-strategy-toolkit.sh strategy validate "{data_root}/strategies/{slug}.json"`.
3. If it fails, patch the error location and message according to the 9 patterns above.
4. Revalidate up to 3 times.
5. If it does not pass within 3 attempts, report the final error and possible alternatives to the user.

---

## User Report Template When the Limit Is Exceeded

If self-correction does not pass within 3 attempts, report in this format and return to STEP 1.

```text
Validation loop limit reached (3 attempts). Self-correction could not resolve it.

Last error:
- Location: {error.loc}
- Message: {error.msg}

Diagnosis:
- {one-line estimated cause}

Possible alternatives:
1. {alternative A}
2. {alternative B}

How should we adjust the hypothesis?
```
