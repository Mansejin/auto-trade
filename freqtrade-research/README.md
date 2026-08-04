# Freqtrade research sandbox — Bitget BTCUSDT-M RSI-BB long/short

## Purpose
Reproduce Upbit toolkit 5m RSI-BB scalp on **Bitget USDT-M futures** with real long+short.

## Rules (frozen v4)
- Long: RSI(14)<25 AND close<BB lower(20,2) AND ADX(14)<30
- Short: RSI(14)>75 AND close>BB upper(20,2) AND ADX(14)<30
- Exit: ROI +0.8% / stoploss -0.3% only
- Fee assumption: taker 0.06% (`fee: 0.0006`)

## Commands
```powershell
cd freqtrade-research
.\.venv\Scripts\freqtrade.exe download-data -c user_data/config.bitget-futures-research.json --trading-mode futures -t 5m --timerange 20260501-20260729
.\.venv\Scripts\freqtrade.exe backtesting -c user_data/config.bitget-futures-research.json --strategy RsiBbScalpLongShortV4 --timerange 20260515-20260529
```

## Guardrails
- Research only. Do not change Policy C / LIVE.
- Do not hyperopt thresholds after seeing results (overfit).

## Regime gate
- Strategy: `RsiBbScalpRegimeGateV1` (bull=long, bear=short, else flat)
- Compare report: `reports/20260729-regime-gate-vs-ungated.md`n

## Sideways MR + ADX switch
- Upbit candidate: `strategies/regime-sideways-mr-1h-adx-switch-v1.json` (not Policy C LIVE)
- Freqtrade: `SidewaysMrAdxSwitchV1` + `config.bitget-sideways-mr.json`
- Report: `reports/20260729-sideways-mr-adx-switch.md`
