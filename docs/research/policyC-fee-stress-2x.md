# Policy C fee stress (2×) — diagnostic

> Map frozen. No retune. OOS segment chain only.

- Baseline OOS: `bt-policyC-oos-presample-20260730_132503.json`
- Stress fee: **0.001** (≈2× 0.05%)
- Segments: 25

| | Baseline (default fee) | Stress 2× fee |
|--|--:|--:|
| Compound return | **+387.40%** | **+319.94%** |
| Multiple | 4.874× | 4.199× |
| Haircut | | -67.45 pp |
| Still profitable? | | **YES** |

## Verdict

Fee doubling does not kill the OOS compound path.

JSON: `reports\bt-policyC-fee-stress-2x-20260730_195305.json`
