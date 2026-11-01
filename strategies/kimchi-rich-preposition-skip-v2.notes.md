# Notes — kimchi-rich-preposition-skip-v2

Monthly automation IMPROVER candidate (2026-11-01). Max 2 param edits from v1.

## Material edits vs v1
1. Buy RSI upper bound: `70` → `55` (reduce chase entries; Oct 2026 v1 WR 33% / PF 0.57)
2. Buy ADX floor: `20` → `23` (align with Policy C bear m5-v6 ADX gate)

No new indicators. Premium-skip / capital routing still external (not in ConditionGroup).

## Hypothesis
Tighter RSI+ADX entry filters reduce overtrading vs v1 without adding complexity tax.

## Falsify
Audit Team gates vs baseline `kimchi-rich-preposition-skip-v1` (`scripts/strategy_audit.py`). Prefer REJECT/HOLD.
