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
