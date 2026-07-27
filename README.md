# auto-trade

업비트 공식 [upbit-strategy-toolkit](https://github.com/upbit-official/upbit-strategy-toolkit) 기반  
**전략 JSON 작성 + 백테스트 리포트** 전용 저장소입니다.

실주문/라이브 봇은 별도 Docker 환경에서 운영합니다. 이 레포에는 API 키·실주문 코드를 두지 않습니다.

## Layout

```text
.
|-- .agents/skills/     # Cursor skills (setup / create-strategy / backtest)
|-- strategies/         # 전략 JSON
|-- reports/            # 백테스트 CSV
`-- cache/              # 캔들 캐시 (gitignore)
```

## Skills 설치 (이미 포함)

프로젝트에 스킬이 포함되어 있습니다. 다른 머신에서 갱신하려면:

```bash
npx skills add upbit-official/upbit-strategy-toolkit -s '*' -a cursor -y --copy
```

## Prerequisites

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

## 현재 전략

| slug | market | timeframe |
|------|--------|-----------|
| `sma-5-20-golden-cross` | KRW-BTC | 1d |

- 가설: SMA(5)가 SMA(20)을 상향 돌파하면 단기 상승이 이어지는 경향이 있다
- 매수: SMA5 `cross_above` SMA20
- 매도: SMA5 `cross_below` SMA20
- 손절/익절: -5% / +15%

## 백테스트 재실행

```bash
export PATH="$HOME/.local/bin:$PATH"
WRAPPER=.agents/skills/backtest/scripts/upbit-strategy-toolkit.sh

bash "$WRAPPER" strategy validate strategies/sma-5-20-golden-cross.json
bash "$WRAPPER" backtest run strategies/sma-5-20-golden-cross.json \
  --start 2025-07-26 --end 2026-07-26
```

## 최근 백테스트 요약 (도구 stdout)

기간 `2025-07-26 ~ 2026-07-26` (UTC), KRW-BTC 1d:

- Benchmark **-40.91%** / Total Return **-17.10%** / MDD **-21.40%**
- Trades **10**, Win Rate **20%**, SL 4 / TP 0 / sell 5 / final_bar 1
- 리포트: `reports/sma-5-20-golden-cross-20260727_154945.csv`

> 슬리피지·호가창 유동성·부분 체결은 반영되지 않습니다.  
> 백테스트 결과는 과거 데이터 기반이며 미래 성과를 보장하지 않습니다.
