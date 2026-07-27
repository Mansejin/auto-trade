# Benchmark Comparison

Guide for interpreting backtest results against **simple market buy-and-hold over the same period** instead of viewing them as standalone values.

---

## 1. Where the Benchmark Comes From

**The tool provides it directly.** The stdout `Benchmark` line prints the simple market buy-and-hold return over the same period. Example:

```
Benchmark   +18.42%
```

The skill only needs to quote this value exactly. **Do not calculate or recalculate it separately.**

---

## 2. Meaning of the Comparison

The benchmark is the baseline for the question, "What if I had simply bought and held the market instead of running the strategy?"

| Comparison result | Meaning (factual statement) |
|---|---|
| total return > benchmark | Strategy return is higher than simple buy-and-hold. Risk-adjusted metrics (Sharpe/MDD) still need to be checked together |
| total return ~= benchmark | Strategy return is similar to simple buy-and-hold. Trade frequency, fees, and drawdown can be compared separately |
| total return < benchmark | Strategy falls short of simple buy-and-hold. Sell signals may have interrupted trend intervals, or entries may have been late |
| total return ~= 0%, benchmark << 0% | Bear-market avoidance effect. Cash intervals in the strategy avoided losses |
| total return >> 0%, benchmark << 0% | Strategy outperformed the benchmark in a bear market over this sample. Sample size and period still need checking |

---

## 3. How to Include It in Reports

**a) Summary section**: the stdout `Benchmark +N.NN%` line is already included. No separate processing.

**c) Comment**: one line for the difference between the two values:

> "Total return +6% / benchmark +18% - 12%p behind simple buy-and-hold. Sell signals may have exited in the middle of trend intervals"

> "Total return -3% / benchmark -22% - loss avoidance in a bear market. However, the sample is only N trades, so generalization needs caution"

**e) `benchmark_comparison` in the handoff payload**:

```
benchmark_comparison: -12.40%p vs benchmark +18.42% (strategy +6.02%)
```

Use signs and units (%p) precisely. "%" and "%p" differ - the difference between returns is **%p (percentage points)**.

---

## 4. Limitations - State to the User

- **Single market only**: the benchmark matches the strategy `market`. If the strategy is KRW-BTC, the benchmark is also KRW-BTC. Altcoin vs BTC comparisons are outside tool scope.
- **Fees not reflected**: the benchmark assumes buy-and-hold and does not calculate fees. Strategy total return is fee-deducted. Keep this difference in mind when comparing the two numbers.
- **Cash intervals not considered**: the benchmark is 100% market exposure. The strategy includes cash intervals - use Sharpe for risk-adjusted comparison.
- **Dimensions beyond return**: the benchmark covers only the return axis. MDD, volatility, trade count, and other dimensions must be checked separately.

State these limitations in roughly **one line at the end of the summary report or in the comment**. Do not explain them at length every time.

---

## 5. Relationship to Hypothesis Falsification Judgment

If `falsification_criterion` is defined as "falsified when below benchmark" (for example, "total return < benchmark"), the benchmark comparison result is the direct input to falsification judgment.

Most hypotheses are defined by win rate or MDD, but benchmark-based falsification is also usable when the core question is whether the strategy outperformed simple buy-and-hold over the tested period.
