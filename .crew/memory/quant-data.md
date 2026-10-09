# quant-data 기억

## 2026-10-08 T-004 카드 5장용 데이터
- 한 일: scripts/data/{_common,fetch_funding,fetch_binance_klines,fetch_upbit_daily,fetch_upbit_announcements,fetch_usdkrw,build_listing_perp_map,verify}.py → data/research/*.csv. 목록은 docs/research/data-catalog.md.
- 환경: httpx·requests 있음, pandas·pyarrow 없음 → stdlib csv만 쓴다. 출력은 parquet이 아니라 CSV.
- 발견:
  - Binance 현물은 상폐 USDT 페어를 exchangeInfo에 status=BREAK로 남기고 REST klines도 준다. vision zip은 대체 경로로만 필요하다(USDT 중 vision에만 있는 건 1개).
  - Upbit 캔들 API는 상폐 마켓에 404 → 상장 이벤트에 생존편향이 생긴다. 공지 API(비공식)의 KRW 상장 공지는 2022-01 이후만 있다.
  - fapi fundingRate는 startTime=0을 무시한다(최근 데이터를 돌려준다). 실제 시작 ms를 넘겨야 한다. 레이트리밋은 500/5분이라 sleep 0.7초.
  - stdout을 파일로 리다이렉트하면 버퍼링돼서 로그가 늦게 찍힌다(진행 확인은 CSV 크기로 한다).
- 다음(T-004): 증분 재실행은 같은 명령을 다시 돌리면 된다.

## 2026-10-08 T-030 oi-flush-rebound 데이터
- 한 일: scripts/data/fetch_oi_metrics.py → data/research/binance_oi_1d.csv (BTC 2020-09-02~, ETH·SOL 2021-12-02~). SOL 무기한 일봉·펀딩은 기존 fetcher에 심볼만 추가. verify.py에 OI 파일 등록.
- 발견:
  - vision `futures/um/daily/metrics` create_time은 REST openInterestHist timestamp보다 5분 이르다(같은 값). +5분 보정해야 00:00 진입에 룩어헤드가 없다. 과거 구간 오프셋은 REST 30일 한계로 미확인.
  - 2020~21 BTC metrics 파일은 행이 두 번씩, 일부 파일에 OI 0 행 → 중복 제거·0 제외. 낡은 스냅샷 날(2022-03-08, 2024-02-17 전 코인)은 원본 파일 자체가 비어 있다.
  - 3코인 ~5,800 zip 다운로드에 12분(0.05초 sleep). s3_list(fetch_binance_klines)로 목록 받기 재사용.
  - Windows: 백그라운드 pwsh 파이프(`| Tee-Object`)를 Stop-Process로 죽이면 python 자식이 살아남아 CSV에 계속 쓴다. 자식 PID까지 죽일 것. 업비트 상폐 마켓 보충이 필요하면 외부 아카이브를 써야 한다(무료 공개 소스는 미확인).

## 2026-10-10 T-037 upbit-caution-perp-short 데이터
- 한 일: fetch_upbit_announcements.py `--category all --start-page --max-pages`(id 병합 이어받기) → upbit_announcements_all 5,880건. build_caution_events.py → upbit_caution_events 93건, caution_perp_symbols.txt 44개 → binance_perp_caution_1d, funding_caution. 자격(공지 전 상장+진입일 거래 중) 32건.
- 안전장치: _common 타임아웃 20초, klines/s3_list/funding 페이징 루프에 PAGE_CAP, get(tries=4). fetch_funding `--slice a:b`로 청크 실행(22심볼 ≈ 105초). 공지 150페이지 ≈ 100초.
- 발견:
  - **상폐 무기한도 fapi REST klines가 거래량 0 평평한 캔들을 오늘까지 준다**, fundingRate도 상폐 뒤 고정값(0.005%) 행이 이어진다(AERGO, LOOM 등). 거래 가능 여부는 `quote_volume`>0으로 판정. 기존 binance_perp_listing_1d에도 같은 문제가 있을 것(T-009 "상폐 무기한 5건" 결함과 같은 원인).
  - exchangeInfo에서 빠진 심볼(AERGO, SXP)은 REST가 400 → vision. vision monthly는 상폐 달이 없을 수 있어 daily zip으로 꼬리 보충(vision_zips에 추가). fetch_binance_klines는 이제 REST가 빈 응답이면 매번 vision을 본다(since 달 이후 zip만 받음).
  - 공지 상세 `GET /api/v1/announcements/<id>`에 body가 있다. 2020~21 "(N종)" 지정 공지는 티커가 본문에만 있다.

## 2026-10-10 T-038 xs-funding-crowding 전체 USDT-M 유니버스
- 한 일: binance_um_universe(906) + binance_um_all_1d(670k행) + funding_um_all(2.78M행). build_um_universe.py가 `tradable` 열·status를 붙인다(재실행 가능, fetch 뒤 항상 다시 돌림). verify.py `um_ghosts()` assert.
- 시간: klines 906개 REST ≈ 4분(청크 2~3개), 펀딩 80심볼 ≈ 225초(500/5분 제한이 병목) → 12청크 ≈ 45분. vision 대체 거의 없음.
- 발견:
  - fapi exchangeInfo는 상폐 무기한을 `SETTLING`으로 남긴다(133개). 주식·원자재는 contractType `TRADIFI_PERPETUAL`(216개) — PERPETUAL만 거르면 vision 목록에서 "vision에만"으로 잘못 잡힌다. `underlyingType`(COIN/EQUITY/…)로 구분.
  - **재상장 티커는 REST klines가 재상장일부터만 준다**(fundingRate는 옛 이력도 줌) → `--backfill-head`로 vision 앞부분 보충. 펀딩 첫 시각 < 캔들 첫 시각이면 의심.
  - fundingRate는 상장 전 기본값 0.01% 행을 준다(BNT 2020-12부터 등). 상장 판정은 캔들 `quote_volume`>0으로.
  - 파생 열을 CSV에 덧붙이면 fetcher append가 열 수가 어긋난다 → _common.append_rows가 기존 헤더 길이만큼 빈칸을 채우게 고침.
