# Famous mount vs Policy C (same regime segments)

Script: `scripts/bt_famous_vs_policyC.py`  
Artifact: `reports/bt-famous-vs-policyC-20260731_040702.json`

Method: classifier segments identical; only strategy map differs; toolkit segment returns compounded.

| Window | Policy C | Famous | B&H |
|--------|---------:|-------:|----:|
| in-sample 2021-07-27→2026-07-26 | **+425.9%** / MDD **−32.2%** | +31.1% / −17.0% | +109% / −74% |
| OOS 2018-04-12→2021-07-24 | **+387.4%** / MDD **−36.7%** | +6.1% / −16.8% | +394% / −67% |

Verdict: Famous does **not** beat Policy C on return (gap ≈ −380~−395%p). Famous MDD is milder (more cash time). CORE restored to Policy C after this race.
