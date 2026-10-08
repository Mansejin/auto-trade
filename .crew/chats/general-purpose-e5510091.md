# general-purpose 대화

- 이어서 부르기: Task resume `e5510091-6b9d-4847-93d9-09083bdb4ed2`

## 요청 Thursday, Oct 8, 2026, 4:32 PM (UTC+9)

Repo: C:\Users\Ohola\Documents\GitHub\auto-trade (Windows, pwsh 7; write files with Write tool, UTF-8, Korean OK).

First read `.cursor/agents/edge-scout.md` and act in that role, and follow `.crew/PROTOCOL.md`. Your task is board item T-001 in `.crew/board.md` (set it to doing at start, done at end with a result line; write memory to `.crew/memory/edge-scout.md`).

Task T-001: Build a full ledger of every strategy this project has ever tested or run.
Sources to scan (read docs/results, do not run backtests): `docs/research/*.md` (many `*-card-frozen.md`), `docs/*.md` playbooks (regime-auto-switch-playbook, scalp-live-playbook, dual-sleeve-allocation, bull-reentry-and-lev-hedge, inbum-diagonal-channel-playbook, KRW-BTC-strategy-pack-agent, system-overview), `freqtrade-research/reports/*.md` and NOTES, `reports/**/*.md` and `reports/*.json` names, `strategies/` (108 files; .json/.notes.md), `freqtrade-research/user_data/strategies/*.py` (66), `VERSION.md`, `scripts/bt_*.py`. Use Grep/Glob efficiently; don't read every file fully — skim headers/verdict sections.

Output `docs/research/strategy-ledger.md` (Korean prose ok, table cells short):
1. Table, one row per strategy/family: 이름 | 데이터 우물 (e.g. OHLCV 캔들패턴 / 박스·채널 / 모멘텀·추세 / 평균회귀 / 레짐 스위치 / 캘린더 이벤트 / 레버리지·차입 / 리밸런스 / 펀딩 등) | 종목·TF | 판정 (KILL / SURVIVE / PARTIAL / LIVE / 미검증) | 핵심 수치 (PF, return, MDD, trades, OOS) | 근거 파일 path.
2. Summary: per data-well count of attempts vs survivors; explicit list of "already-dug wells" (do not re-propose); list of surviving or partially surviving assets with honest caveats. Known: Policy C (regime map bull→regime-bull-trend-4h-v2, bear→m5-v6, sideways→regime-sideways-mr-4h-v5) OOS 2018-2021 +387% vs B&H +394%, MDD -37% vs -67%, survives 2x fee; it is currently CORE live on Upbit. Also note what is live now: w1 Upbit CORE (live), w5 Freqtrade Bitget scalp trend-short (live, config freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json), w2 Bitget SMA (paper).
3. Lessons: 3-6 bullets on why things died (common failure modes).

Return to me: path of the ledger, counts per well, the survivor list, and the top 3 lessons. Keep the final message under 300 words.

## general-purpose

I should first check the role file and protocol to understand the context before proceeding.

## general-purpose

There's a lot to scan through, so I'll grep for verdict lines across the docs/research and freqtrade reports.

## general-purpose

I should check the verdict sections of the freqtrade reports, so I'm going to grep for summary lines across them.

## general-purpose

I should check the remaining research files next—mid-swing, btc-dump-sweep, cal-event sweeps, policyC docs—along with playbooks, VERSION.md, and the strategy/report directory listings to get a full picture.

## general-purpose

Now the playbooks, VERSION.md, and directory listings.

## general-purpose

I should also check the reports/improve files for the alpha AE series like funding and upbit premium, since those are non-OHLCV wells needing verdicts, and grep for verdicts across automation, audit, ops, and the deep-dive NOTES files.

## general-purpose

I still need to dig into AE12's funding hypothesis and lag/event-study details, plus check whether AE13's Upbit premium fade survives fees. I should also look over the kimchi-rich preposition notes, the trend-short leverage-3 and scalp profit-factor threshold notes, and the day-trade strategy out-of-sample report.

## general-purpose

I should check a few more files quickly: the trend-short-lev3 notes, scalp-pf-threshold notes, the bitget BTC short swing README, live-month-review, williams-live-promote, dual-sleeve, weekly-core-obs, more of the five-year README, fair-race, and the docs playbooks.

## general-purpose

I should flag that Policy C was selected in-sample on the 2021-2026 window, which is a caveat worth noting. Now I'll move on to the docs and playbooks, skimming the headers and grepping key status lines from those documents.

## general-purpose

I should check the KRW-BTC pack m5-v6 metrics and its rejected list, the five-year README's standalone falsification note, the dual-sleeve allocation section, the daytrade strategy OOS report, and trace the Williams live promotion history to see when it was replaced.

I also want to look at the scalp-short-edge automation ledger, the SMA cross v0.1 initial notes and Bitget SMA paper trading, and the rebalance weight files for the 10-year backtest and aggressive allocation. Let me pull up a handful of these.

## general-purpose

I should also check the Div ATR daytrade scalp, which went live and then got stopped shortly after, plus skim the live-month-review, williams-live-promote, five-year README, and ae12-lag docs for completeness. I'll glance at the rsi-ichi-checks summary and the rsi-bb-short-v5 and trend-short-v1 searches too, just to confirm coverage.

## general-purpose

There's also the bear-bounce, transition-recovery, and kimchi premium overlay logic to check for live status, plus whether the ATR scalp from 07-30 actually stopped as noted in the briefing. I should pull up scalp-live-map.json and sleeves.json to verify current state alongside the Bitget SMA paper setup.

## general-purpose

There are also other result sets to check — sideways and bull variant comparisons, plus bull-gate and edge-recheck files. I'll grep those for "verdict" to get a quick read without loading everything.

## general-purpose

I want to quickly check the bull-entry/exit comparison JSON for 20260805, maybe grepping for "winner" or "keep" keys, so let me peek at one of the files.

## general-purpose

My regex stripped the dates from the names, so I'll skip the detailed bull entry/exit comparison for v3-v8 and just note that Policy C wasn't adopted, keeping bull-v2 instead. I should quickly glob for the actual filename to cite for the bull-exit comparison.

## general-purpose

I still need the ae12 lag-mdd diagnostic verdict, but more notably, ae12c and AE13b both appear to survive the 20bps fee threshold — the HTX funding signal and the H_rich fade — making them rare partial survivors outside the OHLCV-based wells. I should pull the actual numbers from ae12c and ae13b to confirm.

## general-purpose

AE12's H1 result holds up with the HTX source, but AE7b falsifies against OKX/Bitget given the different source and threshold—so that's a contradiction worth flagging as a caveat. For AE13's premium fade, shorting KRW-BTC on Upbit isn't viable since it's spot-only, so I'll implement it as skipping longs instead, with n=21. I'll skip the AE12-lag-mdd and AE14 checks since lag-mdd is just diagnostic.

I should also check whether the premium_watcher overlay logic for AE12/AE13 is actually live by grepping the docs for its status.

## general-purpose

Policy C's ETH transfer also holds up well, beating buy-and-hold both in-sample and out-of-sample with a shallower drawdown. The classic strategies like Faber's 10-month SMA and Wilder's RSI mean-reversion also perform respectably in-sample, so I'm noting those alongside the rebalancing variants.

The nassi-3tick A/B/C setup isn't technically falsified but its net returns are too thin to matter — basically a practical kill. I still need to check the SMA golden cross filters, the various KRW-BTC m5 families, the scalping strategies on Upbit, and whether there's any report on AltBearShort specifically.

## general-purpose

I'm noting that AltBearShort and Visual5mBearShort have no reports so I'll mark them unverified, and confirming the v1-v5 bear short table coverage looks fine. Now I'm moving to write the ledger file, starting by defining the "wells" categories and rows, beginning with OHLCV candle patterns.

For the tick/bar fade family, most attempts either outright failed or only survived in a formal sense with no real economic edge, so I'm tagging those as "survived formally but economically meaningless" — out of 10 attempts, none are genuine economic survivors. Moving to the box/channel family (box fade, diagonal), I count 14 attempts with zero survivors, since the one weak survivor wasn't promoted. Now I'm going through the mean-reversion/oscillator family (RSI-BB fades, stoch/williams, sideways MR), compiling their backtest results.

I'm uncertain about the Williams 1h status — it was promoted to LIVE around 07-29 as a sideways sleeve, but the current canonical regime map seems to route sideways conditions to 4h-v5 instead, so I'll flag that discrepancy explicitly. I'm also tracking the various sideways 4h/1d variants and 15m BB fade attempts, several of which went LIVE briefly before being parked or killed.

Moving into momentum and trend-following strategies, I'm cataloging the SMA cross family across versions and exchanges, the m5 EMA-ADX group, and the bull-trend 4h variants, noting which versions sit in the current policy and which were killed despite looking viable standalone.

Then I'm going through the AE trend families (AE4, AE9, AE10, AE11), various 4h swing and daytrade pullback strategies, and bear short scalp attempts — nearly all killed by cost or domination — except the TrendShortV1 di_cloud 5m which partially survives but fails at 8bps.

Now I'm reviewing the leverage variants (Lev3, Lev3Px), RSI divergence daytrade edge strategies which I'm classifying as mean-reversion/divergence plays, and the Faber 10-month SMA benchmark. Then moving into regime-switching approaches: Policy C is live, with gating comparisons against ungated scalp and sideways mean-reversion ADX switches mostly killed, plus a race against the Famous strategy where Policy C comes out ahead on returns.

Continuing through Policy C robustness checks — it partially survives an ETH transfer, dies on QQQ, survives doubled fees, and holds up out-of-sample roughly matching buy-and-hold. Then on calendar events, I'm killing the vol-reclaim and mostly killing sweep-fade variants (thin holdout sample), filing the BTC dump sweep fade under liquidity-sweep rather than calendar since it's always-on, and categorizing US-session diagonal filters under candle patterns. Now starting into leverage/borrowing strategies, with borrow R4 and the Lev5 TP nassi variant both getting killed.

Moving on, TrendShort lev3 gets grouped separately and the bull-reentry-and-lev-hedge idea remains untested. For rebalancing/allocation, I'm running through 50:50, 80:20, 70:30 and various weight grids — all underperform Policy C on returns though 50:50 has a better MDD than holding, so the verdict is these are killed as alpha strategies but still valid as treasury rebalancing ops. Then starting into funding/derivatives strategies outside OHLCV data, where AE7 is untestable, AE7b is killed, and AE12's HTX funding variant partially survives with a positive holdout return.

For the orderbook imbalance idea, data isn't ready yet to test it. Moving to kimchi premium strategies, AE13's rich-side variant partially survives fee thresholds with a small sample, the cheap-side variant is killed, and a preposition-skip variant remains untested. Then covering the divergence daytrading family — around 90 cards tested, 5 promoted, but out-of-sample trade counts are too sparse, and the 10-minute divergence-ATR version was live briefly before being stopped due to fees and slippage; I'm filing this as its own row family under mean-reversion rather than merging it in. Now I'm starting to tally up attempt counts per strategy family at the card level.

Running through the candle pattern and sweep family, that's about 11 cards with zero economic survivors. The box and channel family totals 14 cards, also with zero survivors since the V2 version was weak. For mean-reversion and oscillator strategies, I'm tallying up a long list spanning Upbit scalp RSI-BB variants, RSI-Ichimoku versions across multiple timeframes, sideways and Williams families, daytrade fade variants, and the large divergence daytrade set.

That whole bucket lands around 45 named strategies plus roughly 90 divergence cards, and only three partial survivors emerge: sideways-4h-v5, williams-1h, and a sparse 10m-div-atr that I ended up stopping. Moving to momentum and trend strategies, I'm counting SMA, m5, bull-4h, AE9-11, bull-pullback, bear-short, trend-short, and faber families totaling around 61 strategies, with bull-v2 surviving as a sleeve candidate.

Now I'm looking at m5-v6 (bear sleeve only) and TrendShortV1 as a live partial survivor. For regime-switching strategies I'm tallying Policy C, ETH/QQQ transfers, regime gate scalp, ADX switch, famous mount, and policy compare versions across 8 total, with Policy C surviving fully and ETH transfer as a partial. Calendar strategies only yield one partial holdout, and the leverage/borrowing category of 6 strategies produces just one partial survivor, Lev3Px.

Continuing through rebalance (0 of 6 as alpha), funding/derivatives (AE7, AE7b, AE12 variants — 1 partial out of 4), and kimchi premium strategies (AE13 variants, 1 partial of 3), I'm now thinking about how to write the file itself — keeping table cells short, and separately tracking SMA cross strategies: the original Upbit SMA cross, golden cross filtered versions with unverified status, and the Bitget paper SMA strategy. I also want to check what the ACTIVE_STRATEGY file currently contains.

I don't think I need it. Time to write the file now.

## general-purpose

Checking the ETH transfer numbers confirms Policy C's in-sample and out-of-sample gains both beat the hold baseline. Now I'll move on to the board and memory setup.

## general-purpose

I should commit and push per the sync rule, though as a subagent the parent may handle this too. Since other agents might be working concurrently, I'll just commit the specific files I touched to stay safe.

## general-purpose

I wrote the ledger to `docs/research/strategy-ledger.md`: about 160 strategies across 11 data wells, each row with a source path. T-001 is marked done on the board, my memory file is written, and it's committed and pushed to branch `cursor/nas-ft-scalp`, not `main`.

**Counts per well (tried / survived or live / partial):**
- Regime switch: about 10 / 1 (Policy C) / 1 (Policy C on ETH)
- Momentum and trend: about 60 / 2 Policy C sleeves plus TrendShortV1 live / 0
- Mean reversion and divergence: about 45, plus about 90 divergence day-trade cards / 1 sleeve / 3
- Candle patterns: 10 / 0 / 5 (pass the rule but earn about nothing)
- Box and channel: about 14 / 0 / 1
- Calendar events: 2 / 0 / 1
- Leverage and borrowing: about 6 / 0 / 1
- Rebalancing: about 6 / 0 / 0
- Funding rate: 3 / 0 / 1
- Order book: 1 / 0 / 0 (data not collected yet)
- Kimchi premium: 3 / 0 / 1

**Survivors:**
- **Policy C (live, Upbit):** out-of-sample 2018–2021 return matches buy-and-hold (+387% vs +394%), but max drawdown is about half (−37% vs −67%). It survives doubled fees. The 5-year +426% is from the same years the map was chosen on, so it isn't independent evidence.
- **TrendShortV1 (live, Bitget scalp):** profit factor 1.44 and 1.20 on two half-year tests, with only 27 and 33 trades. It fails fee stress at 8 basis points and above.
- **Partial only:** Policy C on ETH; a negative-funding signal on HTX data (it fails on OKX/Bitget data); a high-kimchi-premium fade with only 21 cases; and the Williams 1h sideways strategy.

One thing to check on the server: there's a record of Williams 1h being promoted to live for sideways markets on 07-29, but the canonical map says `regime-sideways-mr-4h-v5`.

**Top 3 lessons:**
1. Fees killed short-timeframe trading. After fees, the best profit factor on 1m and 5m scalps was 0.86–0.93.
2. The same BTC price data was mined over and over: about 90 divergence cards, 13 short versions and 11 channel versions. That produces lucky one-window winners that don't repeat.
3. Strategies left running all the time lost to buy-and-hold (m5-v6 over 5 years: −14% vs +118%). Each one only worked inside the regime map, and even there the edge was lower drawdown, not higher return.
