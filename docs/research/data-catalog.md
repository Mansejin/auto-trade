# 리서치 데이터 카탈로그

T-004 (quant-data, 2026-10-08). 파일은 `data/research/` (gitignored). 스크립트는 `scripts/data/`, 의존성은 표준 라이브러리 + httpx만 사용. 공개 무인증 엔드포인트만.
모든 fetcher는 재실행하면 이어받는다(키별 마지막 시각 이후만 추가). 저장하는 건 마감된 캔들뿐. 점검: `python scripts/data/verify.py`.

시각 규약: 일봉 `date_utc` = UTC 00:00에 열리는 날(업비트 일봉은 09:00 KST = 00:00 UTC라 같은 날로 맞춰진다). 펀딩 `funding_time_*` = **정산 시각**(그 시각에 확정·적용된다. 신호에 쓰려면 정산 시각 이후에만 알 수 있다).

| 이름 (csv) | 출처 | 기간 | 해상도 | 행 수 | 결측 | 재실행 명령 | 쓰는 카드 |
|---|---|---|---|---|---|---|---|
| `funding` | `fapi.binance.com/fapi/v1/fundingRate`, `api.bybit.com/v5/market/funding/history` (linear) | Binance BTC 2019-09-10~, ETH 2019-11-27~; Bybit BTC 2020-03-25~, ETH 2020-10-21~ (~2026-10-08) | 8h 정산 | 28,973 | 9h 넘는 간격 0, 중복 0 | `python scripts/data/fetch_funding.py` | funding-negative-consensus, funding-carry-btc-eth |
| `binance_spot_1d` | `api.binance.com/api/v3/klines` BTC/ETH/XRP USDT | BTC·ETH 2017-08-17~, XRP 2018-05-04~ (~2026-10-07) | 1d | 9,757 | 0 | `python scripts/data/fetch_binance_klines.py --market spot --symbols BTCUSDT,ETHUSDT,XRPUSDT --out binance_spot_1d` | funding-carry, kimchi-rich-fade |
| `binance_perp_1d` | `fapi.binance.com/fapi/v1/klines` BTC/ETH/XRP USDT | BTC 2019-09-08~, ETH 2019-11-27~, XRP 2020-01-06~ | 1d | 7,561 | 0 | `python scripts/data/fetch_binance_klines.py --market perp --symbols BTCUSDT,ETHUSDT,XRPUSDT --out binance_perp_1d` | funding-carry (베이시스) |
| `upbit_krw_1d` | `api.upbit.com/v1/candles/days`, 현재 KRW 마켓 전체(`/v1/market/all`) | 2017-09-25~2026-10-07 | 1d | 324,099 (292개 마켓) | 결측 65일: 2017~18 거래소 점검으로 대부분 3일씩, KRW-ARDR 20일. 상폐 마켓은 404라 **없음** | `python scripts/data/fetch_upbit_daily.py` (`--markets KRW-BTC,...`로 일부만) | kimchi-rich-fade, funding-negative-consensus, upbit-listing-fade |
| `upbit_listings` | `upbit_krw_1d`에서 계산(마켓별 첫 일봉) | 첫 일봉 2017-09-25~ | 이벤트 | 292 (launch_cohort 17개, 2020년 이후 첫 일봉 240개) | 상폐 마켓 없음. 티커 변경(POLY→POLYX, STRAT→STRAX 등)은 예전 이력을 그대로 가져간다 | `fetch_upbit_daily.py`가 같이 만든다 | upbit-listing-fade |
| `upbit_announcements`, `upbit_listing_notices` | `api-manager.upbit.com/api/v1/announcements?category=trade` (비공식) | 공지 785건 2017-10-27~; KRW 상장 공지 211건은 **2022-01-11~**만 | 이벤트(KST) | 785 / 211 | 비공식 API라 2022년 이전 상장 공지가 거의 없다. 제목 정규식으로 파싱 | `python scripts/data/fetch_upbit_announcements.py` | upbit-listing-fade (보조, 상폐 보충) |
| `usdkrw` | `api.frankfurter.app` (ECB 기준환율) | 2017-01-02~2026-10-07 | 영업일 | 2,499 | 주말·TARGET 휴일 없음. 쓸 때 직전 값으로 forward-fill만 하고 back-fill은 하지 않는다 | `python scripts/data/fetch_usdkrw.py` | kimchi-rich-fade |
| `binance_spot_usdt_1d` + `binance_spot_usdt_symbols` | `api.binance.com/api/v3/klines`, 심볼 = `exchangeInfo` USDT(TRADING+BREAK) ∪ `data.binance.vision` spot/monthly/klines 목록, 레버리지 토큰 제외. REST가 거절하면 vision 월별 zip으로 대체 | 2017-08-17~2026-10-07 | 1d | 819,175 (709개 심볼: 거래 중 504, BREAK(상폐) 204, vision에만 있음 1) | 결측 1,130일, 18개 심볼. 대부분 스테이블 코인(TUSD/USDC/USDP 165일)과 상폐 후 재상장(FTT 310일, CVC 153일) | `python scripts/data/fetch_binance_klines.py --market spot --universe --out binance_spot_usdt_1d` | xs-alt-momentum-weekly |
| `listing_perp_map` + `listing_perp_symbols.txt` | `upbit_listings`(2020+, launch_cohort 제외) ∪ `upbit_listing_notices`(2020+) → `fapi exchangeInfo` ∪ vision futures/um 목록. 매칭 순서 XXX, 1000XXX, 1000000XXX, 1MXXX | 2020~ | 매핑 | 티커 250개, 무기한 매칭 207개, 공지에만 있는 것 10개 | 상장 시점에 무기한이 이미 있었는지는 판단하지 않았다. 리서치에서 `perp 첫 일봉 < 업비트 상장일`로 거른다 | `python scripts/data/build_listing_perp_map.py` | upbit-listing-fade |
| `binance_perp_listing_1d` | `fapi.binance.com/fapi/v1/klines` (실패하면 vision futures/um zip) | 2020-01-17~2026-10-07 | 1d | 179,802 (207개 심볼) | 0 | `python scripts/data/fetch_binance_klines.py --market perp --symbols-file data/research/listing_perp_symbols.txt --out binance_perp_listing_1d` | upbit-listing-fade |
| `funding_alts` | `fapi.binance.com/fapi/v1/fundingRate` | 심볼별 상장일~ | 정산마다(대부분 8h, 일부 4h/1h) | 825,303 (207개 심볼) | 9h 간격 점검은 8h 심볼에만 의미가 있다 | `python scripts/data/fetch_funding.py --exchanges binance --symbols-file data/research/listing_perp_symbols.txt --out funding_alts` | upbit-listing-fade |

## 카드별 상태
- **funding-negative-consensus**: 데이터 완비. Binance+Bybit BTC 펀딩 2020-03~ (train 시작과 같다), Upbit KRW-BTC 일봉.
- **funding-carry-btc-eth**: 데이터 완비. 단 Binance ETH 펀딩/무기한은 2019-11-27부터라 train 앞부분의 ETH 구간이 3개월 짧다.
- **kimchi-rich-fade-pooled**: 데이터 완비. USDT≈USD 가정. 디페그 플래그가 필요하면 `binance_spot_usdt_1d`의 USDCUSDT 종가 등으로 대용한다(별도 fetch 없음).
- **xs-alt-momentum-weekly**: 테스트 가능. 생존편향이 크게 줄었다. Binance가 상폐 USDT 페어를 `BREAK` 상태로 남기고 REST로도 이력을 주기 때문이다(vision 목록 757개 중 레버리지 토큰을 빼면 전부 확보, vision에만 있는 건 1개). 남은 편향은 두 가지다. (1) Binance에 한 번도 USDT로 상장되지 않은 코인은 없다. (2) 2017~2019년 초기 유니버스가 작다(USDT 페어 수). 상폐 처리용 마지막 날짜는 `binance_spot_usdt_symbols.csv` status=BREAK + 마지막 `date_utc`로 정한다. 스테이블 코인 제외는 리서치에서 한다.
- **upbit-listing-fade**: 부분. 상장일은 현재 KRW 마켓의 첫 일봉으로 정했다. **상폐된 KRW 마켓은 캔들 API가 404**라 빠지고, 공지 API는 2022년 이후 상장 공지만 있어 보충이 10개 티커에 그친다. 2020~2021 상장 중 이후 상폐된 코인이 없어 펌프 후 하락(=숏에 유리) 이벤트가 덜 잡힐 가능성이 높다. 결과에 명시할 것. 티커 변경은 공지와 대조해야 한다.
