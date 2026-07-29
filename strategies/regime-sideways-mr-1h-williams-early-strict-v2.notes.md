# Williams early-strict v2 (hybrid early band only)

## Role
Used only when `scripts/williams_dwell_gate.py --mode hybrid` and sideways dwell in **7..13**.

## Diff vs base v1
- Entry ADX max: 20 -> **15** (stricter early-stretch confirmation)
- Williams / BB / exits / SL-TP: same as v1

## Note
Develop comparison preferred **dwell7 + base v1** over hybrid for paper.
This JSON kept for optional hybrid experiments — do not retune further on the same windows.
