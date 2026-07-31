# Policy C → Upbit KRW-ETH transfer (research)

> Not investment advice. Research only — **does not** change BTC LIVE Policy C.

| | |
|--|--|
| Market | `KRW-ETH` |
| Script | `scripts/bt_policyC_eth_transfer.py` |
| Map | Same files as BTC fair-race Policy C (bull-v2 / m5-v6 / sideways-v5), `market` swapped to ETH |
| Classifier | regime engine v2 on **ETH** daily |
| Artifact | `reports/bt-policyC-eth-transfer-20260731_042743.json` |

## Result

| Window | Policy C–ETH | ETH hold |
|--------|-------------:|---------:|
| in-sample 2021-07-27→2026-07-26 | **+47.9%** / MDD **−50.6%** | +7.4% / −77.4% |
| OOS 2018-04-12→2021-07-24 | **+615.3%** / MDD **−48.6%** | +403.9% / −89.5% |

Both windows: beats hold on **return** and **MDD**.

## Contrast

| Asset | Transfer note |
|-------|----------------|
| BTC | Home market; strong in-sample, OOS MDD edge / return ≈ hold |
| ETH | Map transfers in this test (both windows beat hold) |
| QQQ (Bitget) | Rejected (−8% vs +13%; short history) |

So Policy C is **not** “BTC-only” in the crypto majors sense; ETH keeps the risk-shaped + return edge here. Still not a LIVE ETH mount without a separate ops decision.

## Guardrails

- No ADX/map retune after seeing results.
- Generated strategies under `strategies/_eth_policyC_xfer/` are ephemeral clones.
