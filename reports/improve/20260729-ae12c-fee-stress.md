# AE12c — Fee stress on AE12b H1 (frozen)

> Same HTX funding cut (`<= -0.0002`), same time holdout (30%).  
> Only cost assumption changes. **No threshold mining. No LIVE promote.**

## Primary gate

Round-trip **20 bps** (≈ Upbit 5+5 fee + ~10 slip). Survive if holdout **net mean > baseline mean** and **gross directional hit > baseline hit**.

## Results

Holdout n=45. Gross mean %=0.3886, hit=0.6444.

| RT bps | Net mean % | Net>0 hit | Gross hit | Base mean | Base hit | Survives |
|-------:|-----------:|----------:|----------:|----------:|---------:|:--------:|
| 10 | 0.2886 | 0.5556 | 0.6444 | -0.0633 | 0.4908 | Y |
| 20 | 0.1886 | 0.5111 | 0.6444 | -0.0633 | 0.4908 | Y |
| 30 | 0.0886 | 0.5111 | 0.6444 | -0.0633 | 0.4908 | Y |
| 50 | -0.1114 | 0.4222 | 0.6444 | -0.0633 | 0.4908 | N |

## Verdict

**SURVIVES_PRIMARY_FEE**

Promotion: **No.** Optional human paper micro-size only if primary survives — still outside Policy C map.

Raw: `reports/improve/ae12c-fee-stress.json`
