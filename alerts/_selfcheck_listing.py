"""Offline self-check for alerts/listing_alert.py:  python -m alerts._selfcheck_listing"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

os.environ["BOT_ROOT"] = tempfile.mkdtemp()
os.environ["LISTING_ALERT_DRY_RUN"] = "true"
from alerts import listing_alert as la  # noqa: E402

stats = json.loads((la.CODE / "config" / "listing-alert-stats.json").read_text(encoding="utf-8"))

# 1000XXX mapping
syms = {"PEPEUSDT", "1000BONKUSDT", "1000000MOGUSDT", "1MBABYDOGEUSDT"}
assert la.match_perp("PEPE", syms) == "PEPEUSDT"
assert la.match_perp("BONK", syms) == "1000BONKUSDT"
assert la.match_perp("MOG", syms) == "1000000MOGUSDT"
assert la.match_perp("BABYDOGE", syms) == "1MBABYDOGEUSDT"
assert la.match_perp("NOPE", syms) == ""

# template rendering: disclaimer always, banned phrase -> fallback, missing var kept
snap = {"binance_symbol": "1000BONKUSDT", "perp_age_days": 400, "quote_volume_musd": 12.3, "funding_pct": 0.01,
        "bybit": "1000BONKUSDT", "bitget": "없음"}
text, rec = la.build_alert("6642", "2026-10-06T20:36:26+09:00", "BONK", "봉크(BONK) 디지털 자산 추가", stats, {}, snap)
assert la.DISCLAIMER in text and "1000BONKUSDT" in text and "1천만~1억 달러" in text and "양(+)" in text and str(stats["ret7_p50_pct"]) in text
assert rec["followup_due_utc"] == "2026-10-14T00:10:00+00:00" and rec["d0_kst"] == "2026-10-06"
nsnap = {"binance_symbol": "", "bybit": "XYZUSDT", "bitget": "없음"}
nop, nrec = la.build_alert("1", "2026-10-06T20:36:26+09:00", "XYZ", "t", stats, {}, nsnap)
assert "해당하지 않아" in nop and "Bybit XYZUSDT" in nop and la.DISCLAIMER in nop
assert la.render("alert", {"ticker": "A"}, {"alert": "{ticker} 지금 매수하세요"}).startswith("[상장 이벤트")
t2 = la.render("alert", {"ticker": "A"}, {"alert": "{ticker} {unknown}"})
assert t2.startswith("A {unknown}") and t2.endswith(la.DISCLAIMER)
for k in la.FALLBACK:
    assert not any(b in la.FALLBACK[k] for b in la.BANNED)

# dedupe: same notice twice, same ticker on another notice, market diff fallback
st = {}
n1 = [("10", "2026-10-06T20:36:26+09:00", "AAA", "x"), ("10", "2026-10-06T20:36:26+09:00", "BBB", "x")]
assert len(la.new_listings(st, n1, {"BTC"}, "now")) == 2
assert la.new_listings(st, n1 + [("11", "t", "AAA", "change notice")], {"BTC", "AAA"}, "now") == []
got = la.new_listings(st, None, {"BTC", "AAA", "CCC"}, "now")
assert [g[2] for g in got] == ["CCC"] and got[0][0] == "market:KRW-CCC"
assert la.new_listings(st, None, {"BTC", "AAA", "CCC"}, "now") == []

# follow-up due logic + tally from append-only record
la.deliver("alert", text, rec)
la.deliver("alert", nop, nrec)  # no perp: recorded, never followed up
recs = la.read_records()
assert la.due_followups(recs, datetime(2026, 10, 13, tzinfo=timezone.utc)) == []
assert [r["ticker"] for r in la.due_followups(recs, datetime(2026, 10, 14, 1, tzinfo=timezone.utc))] == ["BONK"]
res = {"ret_7d_pct": -12.0, "high_7d_pct": 5.0, "price_source": "x", "entry_date": "2026-10-07", "exit_date": "2026-10-14"}
fv = la.followup_vars(recs[0], res, recs, stats)
assert fv["fwd_n"] == 1 and fv["fwd_fell_n"] == 1 and fv["fwd_fell_share_pct"] == 100 and fv["fwd_missed_n"] == 0
assert fv["ret_vs_median_pp"] == f"{-12.0 - stats['ret7_p50_pct']:+.1f}"
fu = la.render("followup", fv, {})
assert "{" not in fu and la.DISCLAIMER in fu
la.deliver("followup", fu, {"ticker": "BONK", "notice_id": "6642", "result": res})
recs = la.read_records()
assert la.due_followups(recs, datetime(2026, 12, 1, tzinfo=timezone.utc)) == []
assert [r["kind"] for r in recs] == ["alert", "alert", "followup"] and all(r["dry_run"] and r["message_hash"] for r in recs)
assert la.followup_vars(recs[0], None, recs, stats)["fwd_missed_n"] == 1
assert "{" not in text and "{" not in nop

# Binance lookup failed at alert time -> eligible, perp rechecked at follow-up (absent -> skipped, not tallied)
la.RECORD.unlink()
utext, urec = la.build_alert("7", "2026-09-01T12:00:00+09:00", "UNK", "t", stats, {}, {"binance_symbol": "", "binance_error": "503"})
assert "확인 실패" in utext and "해당하지 않아" not in utext
la.deliver("alert", utext, urec)
la.binance_perp = lambda t, at: ("", None)
la.run_followups(stats, {})
la.run_followups(stats, {})
assert [r["kind"] for r in la.read_records()] == ["alert", "followup_skipped"]

print("listing alert selfcheck OK\n---\n" + text + "\n---\n" + fu)
Path(la.RECORD).unlink()
