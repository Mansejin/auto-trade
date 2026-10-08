"""QA tests for alerts/listing_alert.py (T-014):  python -m alerts._test_listing_alert

Offline except the replay section (live Binance/Bybit/Bitget; LISTING_TEST_OFFLINE=1 skips it).
Each check runs isolated (fresh BOT_ROOT files); failures are reported, not raised, so the summary counts all.
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

os.environ["BOT_ROOT"] = tempfile.mkdtemp()
os.environ["LISTING_ALERT_DRY_RUN"] = "true"
from alerts import listing_alert as la  # noqa: E402

STATS = json.loads(la.STATS.read_text(encoding="utf-8"))
TEMPLATES = la.load_templates()
NOW_KST = datetime.now(la.KST).isoformat(timespec="seconds")
PERP = {"binance_symbol": "AAAUSDT", "perp_age_days": 100, "quote_volume_musd": 5.0, "funding_pct": 0.01,
        "bybit": "AAAUSDT", "bitget": "없음"}
NOPERP = {"binance_symbol": "", "bybit": "없음", "bitget": "없음"}
RESULTS: list[tuple[str, str]] = []


class NoTelegram:
    def __init__(self, *a, **k):
        raise AssertionError("TelegramNotifier constructed in DRY_RUN")


class SpyTelegram:
    sent: list[str] = []

    def __init__(self, *a, **k):
        pass

    def send(self, text):
        SpyTelegram.sent.append(text)
        return True


ORIG = {k: getattr(la, k) for k in ("fetch_listing_notices", "fetch_krw_markets", "snapshot", "seven_day",
                                     "get", "TelegramNotifier", "DRY_RUN", "TEMPLATES", "run_followups")}


def reset(notices=(), krw=("BTC",), snaps=None, seven=None):
    """Fresh files + fakes. notices: list or Exception instance."""
    for k, v in ORIG.items():
        setattr(la, k, v)
    for p in (la.STATE, la.RECORD, la.STATE.with_suffix(".tmp")):
        p.unlink(missing_ok=True)
    box = {"notices": notices, "krw": set(krw)}

    def fn():
        if isinstance(box["notices"], Exception):
            raise box["notices"]
        return list(box["notices"])
    la.fetch_listing_notices = fn
    la.fetch_krw_markets = lambda: set(box["krw"])
    la.snapshot = lambda t, at: dict((snaps or {}).get(t, PERP))
    la.seven_day = seven or (lambda sym, d0: {"ret_7d_pct": -10.0, "high_7d_pct": 3.0, "price_source": f"Binance {sym}",
                                               "entry_date": str(d0 + timedelta(1)), "exit_date": str(d0 + timedelta(8))})
    la.TelegramNotifier = NoTelegram
    return box


def recs(kind=None):
    return [r for r in la.read_records() if kind is None or r.get("kind") == kind]


def raw():
    return la.RECORD.read_bytes() if la.RECORD.exists() else b""


def poll(prev: bytes) -> bytes:
    """run_once and assert the jsonl only grew (old bytes are an exact prefix)."""
    la.run_once()
    now = raw()
    assert now.startswith(prev) and len(now) >= len(prev), "listing-alerts.jsonl was rewritten"
    return now


def check(name):
    def deco(fn):
        try:
            fn()
            RESULTS.append((name, "PASS"))
        except Exception as e:
            RESULTS.append((name, f"FAIL: {type(e).__name__}: {e}"))
            traceback.print_exc()
        return fn
    return deco


def notice(nid, t, at=None):
    return (str(nid), at or NOW_KST, t, f"테스트({t}) KRW 마켓 디지털 자산 추가")


# ---------------------------------------------------------------- replay (live network)
@check("replay 3 past listings (live)")
def _():
    if os.getenv("LISTING_TEST_OFFLINE") == "1":
        raise RuntimeError("skipped by LISTING_TEST_OFFLINE=1")
    reset()
    la.snapshot, la.get = ORIG["snapshot"], ORIG["get"]
    rows = {r["ticker"]: r for r in csv.DictReader(open(la.CODE / "data/research/upbit_listing_notices.csv", encoding="utf-8"))}
    for t in ("NMR", "CASHCAT", "POD"):
        r = rows[t]
        text, rec = la.build_alert(r["id"], r["announced_at_kst"], t, r["title"], STATS, TEMPLATES, alert_id="R")
        print(f"--- replay {t}: binance={rec['snapshot'].get('binance_symbol')!r} bybit={rec['snapshot'].get('bybit')} "
              f"bitget={rec['snapshot'].get('bitget')} err={rec['snapshot'].get('binance_error', '')}")
        assert la.DISCLAIMER in text and "{" not in text and not any(b in text for b in la.BANNED), t
        assert ("해당하지 않아" in text) == (not rec["snapshot"].get("binance_symbol")), t
        assert f"id={r['id']}" in text and t in text
    assert raw() == b"", "build_alert (replay) must not record"


@check("live seven_day == frozen stats bars (1 OOS event)")
def _():
    if os.getenv("LISTING_TEST_OFFLINE") == "1":
        raise RuntimeError("skipped by LISTING_TEST_OFFLINE=1")
    ev = [e for e in json.loads((la.CODE / "reports/research-cards/upbit-listing-fade.json").read_text(encoding="utf-8"))["events"]
          if e["listing"] >= "2023-07-01"][-1]
    bars = {}
    for r in csv.DictReader(open(la.CODE / "data/research/binance_perp_listing_1d.csv", encoding="utf-8")):
        if r["symbol"] == ev["sym"]:
            bars[date.fromisoformat(r["date_utc"][:10])] = float(r["open"])
    e0 = date.fromisoformat(ev["entry"])
    want = round((bars[e0 + timedelta(7)] / bars[e0] - 1) * 100, 1)
    got = ORIG["seven_day"](ev["sym"], date.fromisoformat(ev["listing"]))
    print(f"--- {ev['ticker']} {ev['sym']} live={got} csv={want}")
    assert got and abs(got["ret_7d_pct"] - want) <= 0.1, (got, want)


# ---------------------------------------------------------------- offline
@check("bootstrap does not alert existing notices")
def _():
    reset([notice(1, "OLD")])
    b = poll(b"")
    assert [r["kind"] for r in recs()] == ["bootstrap"] and recs("bootstrap")[0]["skipped"] == ["1:OLD"]
    poll(b)
    assert recs("alert") == []


@check("notice API failure: one failure line, no crash, no duplicate later")
def _():
    box = reset([notice(1, "OLD")])
    b = poll(b"")
    box["notices"] = RuntimeError("HTTP 503")
    b = poll(b)
    b = poll(b)
    assert len(recs("source_down")) == 1, recs("source_down")
    box["krw"] = {"BTC", "NEW"}            # listing appears while notices are down -> market-diff alert
    b = poll(b)
    box["notices"] = [notice(1, "OLD"), notice(2, "NEW")]  # API back with the same listing
    b = poll(b)
    b = poll(b)
    alerts = recs("alert")
    assert [a["ticker"] for a in alerts] == ["NEW"] and alerts[0]["notice_id"] == "market:KRW-NEW", alerts
    assert len(recs("source_recovered")) == 1


@check("notice API failure during bootstrap: one failure line across polls")
def _():
    reset(RuntimeError("HTTP 503"))
    b = poll(b"")
    b = poll(b)
    b = poll(b)
    n = len(recs("source_down"))
    assert n == 1, f"{n} source_down lines after 3 failing bootstrap polls (each also counts as fwd_missed)"


@check("duplicate notice id -> one alert")
def _():
    box = reset([])
    b = poll(b"")
    box["notices"] = [notice(5, "DUP"), notice(5, "DUP")]
    b = poll(b)
    b = poll(b)
    box["notices"] = [notice(6, "DUP")]   # later "change" notice for the same ticker
    b = poll(b)
    assert [a["ticker"] for a in recs("alert")] == ["DUP"]


@check("perp absent: no stats, recorded, excluded from follow-up/tally")
def _():
    box = reset([], snaps={"NOP": NOPERP, "YES": PERP})
    b = poll(b"")
    box["notices"] = [notice(7, "NOP", "2026-09-01T12:00:00+09:00"), notice(8, "YES", "2026-09-01T12:00:00+09:00")]
    b = poll(b)
    nop = next(a for a in recs("alert") if a["ticker"] == "NOP")
    assert "해당하지 않아" in nop["message"] and "집계에서 제외" in nop["message"] and la.DISCLAIMER in nop["message"]
    assert str(STATS["ret7_p50_pct"]) not in nop["message"] and str(STATS["n"]) + "건" not in nop["message"]
    b = poll(b)
    fus = recs("followup")
    assert [f["ticker"] for f in fus] == ["YES"], fus
    assert "누적 1건" in fus[0]["message"]
    assert la.due_followups(la.read_records(), datetime(2030, 1, 1, tzinfo=timezone.utc)) == []


@check("Binance lookup failure is not reported as 'perp absent'")
def _():
    reset()
    la.snapshot = ORIG["snapshot"]

    def get(url, params=None, **k):
        if "fapi.binance.com" in url:
            raise RuntimeError("binance 503")
        return {}
    la.get = get
    snap = la.snapshot("AAA", datetime(2026, 10, 1, tzinfo=timezone.utc))
    text, _ = la.build_alert("9", "2026-10-01T12:00:00+09:00", "AAA", "t", STATS, TEMPLATES, snap)
    assert "binance_error" in snap
    assert "Binance 없음" not in text and "해당하지 않아" not in text, \
        "Binance API outage rendered as 'Binance 없음 / 과거 표본에 해당하지 않아' and excluded from tally"


@check("1000XXX mapping + onboard-before-alert rule")
def _():
    reset()
    la.snapshot = ORIG["snapshot"]
    at = datetime(2026, 10, 1, tzinfo=timezone.utc)
    onboard = {"1000BONKUSDT": at - timedelta(days=400), "1000000MOGUSDT": at + timedelta(hours=1)}

    def get(url, params=None, **k):
        if url.endswith("/exchangeInfo"):
            return {"symbols": [{"symbol": s, "contractType": "PERPETUAL", "quoteAsset": "USDT", "status": "TRADING",
                                 "onboardDate": int(o.timestamp() * 1000)} for s, o in onboard.items()]}
        if url.endswith("/ticker/24hr"):
            return {"quoteVolume": "12345678"}
        if url.endswith("/premiumIndex"):
            return {"lastFundingRate": "0.0001"}
        return {}
    la.get = get
    s = la.snapshot("BONK", at)
    assert s["binance_symbol"] == "1000BONKUSDT" and s["perp_age_days"] == 400 and s["quote_volume_musd"] == 12.3
    assert s["funding_pct"] == 0.01 and s["bybit"] == "없음"
    assert la.snapshot("MOG", at)["binance_symbol"] == ""          # onboarded after the alert
    assert la.match_perp("BONK", {"BONKUSDT", "1000BONKUSDT"}) == "BONKUSDT"
    assert la.match_perp("SATS", {"1000SATSUSDT"}) == "1000SATSUSDT"


@check("follow-up due exactly at D+8 00:10 UTC, not before; seven_day open D+1 -> open D+8")
def _():
    reset()
    text, rec = la.build_alert("1", "2026-10-06T23:59:00+09:00", "AAA", "t", STATS, {}, dict(PERP))
    rec = {**rec, "kind": "alert"}
    due = datetime.fromisoformat(rec["followup_due_utc"])
    assert due == datetime(2026, 10, 14, 0, 10, tzinfo=timezone.utc)
    assert la.due_followups([rec], due - timedelta(seconds=1)) == []
    assert la.due_followups([rec], due) == [rec]
    d0 = date(2026, 10, 6)
    bars = [[la._ms(d0 + timedelta(i)), str(100 + i), str(110 + i), "0", "0"] for i in range(1, 9)]
    la.get = lambda url, params=None, **k: bars if params["startTime"] == la._ms(d0 + timedelta(1)) else []
    r = ORIG["seven_day"]("AAAUSDT", d0)
    assert r["ret_7d_pct"] == round((108 / 101 - 1) * 100, 1) and r["entry_date"] == "2026-10-07" and r["exit_date"] == "2026-10-14", r
    assert r["high_7d_pct"] == round((117 / 101 - 1) * 100, 1)       # max high D+1..D+7 only
    la.get = lambda url, params=None, **k: bars[:-1]                 # D+8 bar not printed yet
    assert ORIG["seven_day"]("AAAUSDT", d0) is None


@check("restart: state reload does not resend; follow-ups not duplicated")
def _():
    box = reset([])
    b = poll(b"")
    box["notices"] = [notice(3, "RST", "2026-09-01T12:00:00+09:00")]
    b = poll(b)
    shutil.copy(la.STATE, la.STATE.with_name("bak.json"))
    for _ in range(3):                    # "restarts": state is re-read from disk each poll
        b = poll(b)
    assert len(recs("alert")) == 1 and len(recs("followup")) == 1
    la.STATE.unlink()                     # state lost -> bootstrap again, must not resend
    b = poll(b)
    assert len(recs("alert")) == 1 and len(recs("followup")) == 1


@check("kill between alert append and state save -> no duplicate alert")
def _():
    box = reset([])
    b = poll(b"")
    box["notices"] = [notice(4, "KIL")]

    def boom(*a):
        raise RuntimeError("simulated crash/kill after alerts were appended")
    la.run_followups = boom
    try:
        la.run_once()
    except RuntimeError:
        pass
    la.run_followups = ORIG["run_followups"]
    poll(raw())
    n = len(recs("alert"))
    assert n == 1, f"{n} alerts for one notice: state is saved only at the end of run_once"


@check("DRY_RUN never constructs TelegramNotifier")
def _():
    reset()
    assert la.DRY_RUN is True
    text, rec = la.build_alert("1", NOW_KST, "AAA", "t", STATS, TEMPLATES, dict(PERP))
    la.deliver("alert", text, rec)
    la.deliver("followup", "x " + la.DISCLAIMER, {"ticker": "AAA", "notice_id": "1", "result": None})
    assert all(r["dry_run"] is True and r["sent"] is False for r in recs())


@check("DRY_RUN -> LIVE switch does not send follow-ups for unpublished dry-run alerts")
def _():
    box = reset([])
    b = poll(b"")
    box["notices"] = [notice(11, "DRY", "2026-09-01T12:00:00+09:00")]
    la.run_followups = lambda *a: None
    b = poll(b)                           # dry-run alert recorded, follow-up not yet run
    la.run_followups = ORIG["run_followups"]
    la.DRY_RUN, la.TelegramNotifier, SpyTelegram.sent = False, SpyTelegram, []
    la.run_followups(STATS, TEMPLATES)
    assert SpyTelegram.sent == [], f"live follow-up sent for dry-run alert: {SpyTelegram.sent[0][:40]!r}"


@check("templates.json missing/broken -> fallback with disclaimer")
def _():
    reset()
    for content in (None, "{not json"):
        p = Path(os.environ["BOT_ROOT"]) / "tpl.json"
        p.unlink(missing_ok=True)
        if content:
            p.write_text(content, encoding="utf-8")
        la.TEMPLATES = p
        tpl = la.load_templates()
        assert tpl == {}
        a, _ = la.build_alert("1", NOW_KST, "AAA", "t", STATS, tpl, dict(PERP))
        n, _ = la.build_alert("1", NOW_KST, "AAA", "t", STATS, tpl, dict(NOPERP))
        f = la.render("followup", la.followup_vars({"ticker": "AAA", "sent_at": "2026-10-01T00:00:00+00:00"},
                                                    None, [], STATS), tpl)
        for t in (a, n, f):
            assert la.DISCLAIMER in t and "{" not in t and not any(x in t for x in la.BANNED)
    assert la.render("alert", {}, {"alert": "no disclaimer here"}).endswith(la.DISCLAIMER)


@check("banned phrases: templates/fallback clean, dirty template falls back")
def _():
    reset()
    assert TEMPLATES and set(TEMPLATES) >= {"alert", "alert_no_perp", "followup"}
    for src in (TEMPLATES, la.FALLBACK):
        for k, v in src.items():
            assert not any(b in v for b in la.BANNED), k
            assert "매수" not in v and "매도" not in v, k
            assert la.DISCLAIMER in v or src is la.FALLBACK, k
    t = la.render("alert_no_perp", {"ticker": "A"}, {"alert_no_perp": "{ticker} 목표가 2배"})
    assert "목표가" not in t and la.DISCLAIMER in t


@check("all recorded messages: disclaimer, no banned phrase, valid json lines")
def _():
    box = reset([], snaps={"N1": NOPERP})
    b = poll(b"")
    box["notices"] = [notice(20, "P1", "2026-09-01T12:00:00+09:00"), notice(21, "N1")]
    b = poll(b)
    for r in recs():
        if "message" in r:
            assert la.DISCLAIMER in r["message"] and not any(x in r["message"] for x in la.BANNED), r["kind"]
            assert "{" not in r["message"], r["message"]
    assert {r["kind"] for r in recs()} >= {"alert", "followup"}


@check("stats file == rerun of scripts/build_listing_alert_stats.py")
def _():
    orig = la.STATS.read_bytes()
    try:
        p = subprocess.run([sys.executable, str(la.CODE / "scripts/build_listing_alert_stats.py")],
                           capture_output=True, text=True, encoding="utf-8", cwd=la.CODE)
        assert p.returncode == 0, p.stderr
        assert json.loads(la.STATS.read_text(encoding="utf-8")) == json.loads(orig)
    finally:
        la.STATS.write_bytes(orig)


def _hist_rets():
    ev = [e for e in json.loads((la.CODE / "reports/research-cards/upbit-listing-fade.json").read_text(encoding="utf-8"))["events"]
          if e["listing"] >= "2023-07-01"]
    syms, bars = {e["sym"] for e in ev}, {}
    for r in csv.DictReader(open(la.CODE / "data/research/binance_perp_listing_1d.csv", encoding="utf-8")):
        if r["symbol"] in syms:
            bars.setdefault(r["symbol"], {})[date.fromisoformat(r["date_utc"][:10])] = float(r["open"])
    return [bars[e["sym"]][date.fromisoformat(e["entry"]) + timedelta(7)] / bars[e["sym"]][date.fromisoformat(e["entry"])] - 1
            for e in ev]


@check("'fell' tally: stats (raw<0) == follow-up rule on the same history")
def _():
    rets = _hist_rets()
    raw_fell = sum(r < 0 for r in rets)
    fu_fell = sum(round(r * 100, 1) < 0 for r in rets)  # follow-up counts seven_day's rounded ret_7d_pct < 0
    print(f"--- history n={len(rets)} fell raw={raw_fell} rounded={fu_fell} (published: 93/133)")
    assert len(rets) == STATS["n"] and fu_fell == raw_fell


@check("published baseline '93/133 fell' matches the price-only definition")
def _():
    raw_fell = sum(r < 0 for r in _hist_rets())
    assert raw_fell == 93, f"open D+1 -> open D+8 gives {raw_fell}/133 fell; docs/sales publish 93/133"


@check("'fell' tally edge: -0.04% counts as fell in follow-up (same as stats raw<0)")
def _():
    reset()
    d0 = date(2026, 10, 6)
    bars = [[la._ms(d0 + timedelta(i)), "100" if i < 8 else "99.96", "101", "0", "0"] for i in range(1, 9)]
    la.get = lambda url, params=None, **k: bars
    res = ORIG["seven_day"]("AAAUSDT", d0)
    fv = la.followup_vars({"ticker": "AAA"}, res, [], STATS)
    assert fv["fwd_fell_n"] == 1, f"raw -0.04% -> ret_7d_pct={res['ret_7d_pct']!r}, fell={fv['fwd_fell_n']}"


@check("fwd_missed_n counts only missed alerts, not market_all outages")
def _():
    box = reset([])
    b = poll(b"")
    la.fetch_krw_markets = lambda: (_ for _ in ()).throw(RuntimeError("market/all 503"))
    b = poll(b)
    fv = la.followup_vars({"ticker": "AAA"}, {"ret_7d_pct": -1.0}, la.read_records(), STATS)
    assert fv["fwd_missed_n"] == 0, f"fwd_missed_n={fv['fwd_missed_n']} after a market/all outage with no listing"


if __name__ == "__main__":
    for k, v in ORIG.items():
        setattr(la, k, v)
    print("\n=== listing alert QA ===")
    for n, r in RESULTS:
        print(f"{'PASS' if r == 'PASS' else 'FAIL'}  {n}" + ("" if r == "PASS" else f"\n      {r[6:]}"))
    fails = sum(r != "PASS" for _, r in RESULTS)
    print(f"\n{len(RESULTS) - fails} passed, {fails} failed")
    shutil.rmtree(os.environ["BOT_ROOT"], ignore_errors=True)
    sys.exit(1 if fails else 0)
