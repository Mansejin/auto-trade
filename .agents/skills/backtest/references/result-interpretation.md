# Result Interpretation Guide

Principles, examples, and falsification-judgment flow for turning `run_backtest()` results into a report. Details for SKILL.md STEP 4.

---

## 1. Factual Statements vs Judgment

**Factual statements (OK)** - state the relationship between two values, or the value's position itself:

- "MDD 23% > stop-loss 5% - drawdown accumulated across positions even though each position's stop-loss was capped at 5%"
- "Among 12 executed trades, SL 8 / TP 2 - stop-loss fired 4 times more often than take-profit"
- "Sharpe(trades) 0.4 < Sharpe(portfolio) 1.1 - cash-holding intervals outside positions reduced volatility"
- "Benchmark +18% / total return +6% - 12%p behind simple KRW-BTC buy-and-hold over the same period"

**Judgment (forbidden)** - evaluative words and adjectives:

- ~~"Performance is good / bad"~~
- ~~"This is an excellent strategy"~~
- ~~"The return is satisfactory"~~
- ~~"This looks like a failed strategy"~~

Judgment belongs to the user. The skill presents facts cleanly so the user can decide.

---

## 2. Report Format

### a) Summary

```
{paste format_result() stdout exactly - do not change even one line}

CSV: {data_root}/reports/{slug}-{YYYYMMDD_HHMMSS}.csv
Hypothesis: {Mode A only - one-sentence hypothesis from STEP 1}
Falsification criterion: {Mode A only - falsification_criterion}
```

The key point is direct stdout quotation. The skill does not recalculate values into a table.

### b) Trade Highlights

Read CSV `# section: trades` and extract the following when available:

- **First entry**: `entry_dt` / `entry_price` / `exit_reason`
- **Highest-profit trade**: maximum `pnl_pct`
- **Largest-loss trade**: minimum `pnl_pct`
- **exit_reason distribution**: `SL N / TP N / sell N / final_bar N` (if already in stdout, quoting stdout is enough)
- **Meaningful pattern**: for example, "TP 0, SL 8" -> one-line comment

If there are 0 trades, state "0 executed trades. Entry signals did not occur, or they were ignored because they were below min_order."
If stdout shows `Win Rate N/A (0 executed trades)` or `Profit Factor  N/A (0 executed trades)`, treat them as undefined because no trades were executed, not as numeric zero or infinity.

### c) Comment (1-2 Lines, Factual Statements)

Point out only one or two relationships between values. Good comment forms:

- "{X value} is {greater/less} than {Y value} - {one-line reason estimate}"
- "Based on {exit_reason distribution}, {signal/take-profit/stop-loss} dominates"

**Examples**:

| Situation | Comment (factual statement) |
|---|---|
| MDD 22% / stop-loss 5% / 30 trades | "MDD is 4x the stop-loss width - losses accumulated after entry during intervals where stop-loss did not fire" |
| win rate 70% / total return -3% | "Win rate is high but total return is negative - one or two large losses offset many small take-profits" |
| SL 0 / TP 0 / sell 12 | "SL/TP did not fire; all exits were sell exits - stop/take-profit lines were not reached before sell signals" |
| benchmark +30% / total return +5% | "Simple buy-and-hold was larger over the same period - sell signals may have interrupted trend intervals" |
| Profit Factor "∞" | "0 losing trades - the sample may be small, or only take-profit/signal exits fired" |
| Win Rate / Profit Factor `N/A (0 executed trades)` | "No trades were executed, so win rate and profit factor are undefined for this sample" |

**Avoid**:
- Evaluating a single value with adjectives ("MDD is large", "Sharpe is low")
- Making absolute-rule claims ("Sharpe below 1.5 is bad") - meaning differs by market and timeframe

### d) Hypothesis Falsification Judgment (Mode A Only)

`falsification_criterion` is the measurable condition agreed with the user in STEP 1. Compare result values directly with that condition and state one of **falsified / retained / inconclusive**.

**Judgment flow**:

1. Decompose `falsification_criterion` into OR/AND clauses (for example, "win rate < 40% **or** MDD > 25%" -> two OR clauses)
2. Substitute each clause's left and right sides with result values
3. If any clause is satisfied -> **falsified**
4. If all clauses are unsatisfied -> **retained**
5. If result values cannot be compared (0 trades, NaN, etc.) -> **inconclusive**

**Example 1 (falsified)**:
```
Falsification criterion: win rate < 40% or MDD > 25%
Result: win rate 32% / MDD 18%
-> falsified: "win rate 32% < 40% is satisfied"
```

**Example 2 (retained)**:
```
Falsification criterion: win rate < 40% or MDD > 25%
Result: win rate 58% / MDD 12%
-> retained: "both clauses are unsatisfied - hypothesis is not falsified. If the sample is only N trades, an additional-period check may still be useful"
```

**Example 3 (inconclusive)**:
```
Falsification criterion: win rate < 40% or MDD > 25%
Result: 0 executed trades
-> inconclusive: "no entries occurred, so the hypothesis cannot be tested. Review entry strictness and the tested period as follow-up checks"
```

**Important**: falsification judgment rejects the hypothesis, not the strategy. Follow-up notes should be framed as neutral revision candidates or additional checks, not as trading recommendations.

> The Mode A/B branching rule itself (which mode states or omits falsification judgment, and whether a handoff payload is required) is stated once in SKILL.md STEP 4. This document treats that rule as a **precondition** and only covers report-format details.
