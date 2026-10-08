"""Upbit KRW listing event alert (docs/product/upbit-listing-alert-brief.md). Information only: no orders.

  python -m alerts.listing_alert                 # poll loop
  python -m alerts.listing_alert --once          # one poll
  python -m alerts.listing_alert --replay NMR 2026-10-06T20:36:26+09:00   # render only, no send/record

Env: BOT_ROOT (default repo root), LISTING_ALERT_POLL_MINUTES=3, LISTING_ALERT_DRY_RUN=true,
LISTING_ALERT_CHAT_ID, TELEGRAM_BOT_TOKEN.
Files: data/listing-alert-state.json (seen ids), logs/listing-alerts.jsonl (append-only public record),
config/listing-alert-stats.json (frozen history, scripts/build_listing_alert_stats.py),
docs/sales/upbit-listing-alert/templates.json (optional; keys alert, alert_no_perp, followup).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import statistics
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "scripts" / "data"))
from fetch_upbit_announcements import LISTING, TICKER, URL as NOTICE_URL  # noqa: E402
from _common import get  # noqa: E402

from bot.telegram_notify import TelegramNotifier  # noqa: E402

log = logging.getLogger("listing_alert")
KST = timezone(timedelta(hours=9))
ROOT = Path(os.getenv("BOT_ROOT") or CODE)
STATE = ROOT / "data" / "listing-alert-state.json"
RECORD = ROOT / "logs" / "listing-alerts.jsonl"
STATS = CODE / "config" / "listing-alert-stats.json"
TEMPLATES = CODE / "docs" / "sales" / "upbit-listing-alert" / "templates.json"
DRY_RUN = os.getenv("LISTING_ALERT_DRY_RUN", "true").strip().lower() not in ("0", "false", "no", "off")
POLL_MIN = float(os.getenv("LISTING_ALERT_POLL_MINUTES", "3"))
DELAY_MIN = float(os.getenv("LISTING_ALERT_DELAY_MINUTES", "0"))
FAPI = "https://fapi.binance.com/fapi/v1"

RECORD_URL = os.getenv("LISTING_ALERT_RECORD_URL", "(공개 기록 주소 준비 중)")

DISCLAIMER = "※ 과거 분포일 뿐 이 코인의 결과를 예측하지 않습니다. 투자 권유 아님, 원금 손실 가능."
BANNED = ("매수하세요", "매도하세요", "진입하세요", "숏 치", "롱 치", "목표가", "손절가", "수익 보장")
# variable names follow docs/sales/upbit-listing-alert/templates.json
FALLBACK = {
    "alert": (
        "[상장 이벤트 #{alert_id}] {ticker}\n공지: {notice_title}\n시각: {notice_time_kst} KST\n원문: {notice_url}\n\n"
        "해외 무기한: Binance {perp_binance} / Bybit {perp_bybit} / Bitget {perp_bitget}\n"
        "무기한 상장 {perp_age_days}일째 · 24h 거래대금 {quote_volume_24h} · 펀딩 {funding_rate_pct} ({funding_source})\n\n"
        "과거 비슷한 상장 {hist_n}건, 다음 날부터 7일 가격 변화\n"
        "하위10% {hist_p10_pct}% · 중앙 {hist_p50_pct}% · 상위10% {hist_p90_pct}%\n"
        "7일 안에 +30% 이상 오른 경우: {hist_up30_share_pct}%\n\n{disclaimer}"
    ),
    "alert_no_perp": (
        "[상장 이벤트 #{alert_id}] {ticker}\n공지: {notice_title}\n시각: {notice_time_kst} KST\n원문: {notice_url}\n\n"
        "해외 무기한: Binance {perp_binance} / Bybit {perp_bybit} / Bitget {perp_bitget}\n"
        "과거 표본(Binance 무기한이 이미 있던 상장)에 해당하지 않아 분포를 붙이지 않습니다.\n\n{disclaimer}"
    ),
    "followup": (
        "[7일 결과 #{alert_id}] {ticker}\n원 알림: {alert_sent_kst} KST 발송\n"
        "{entry_date} 시가 → {exit_date} 시가 (UTC 일봉): {ret_7d_pct}%\n"
        "과거 중앙값 {hist_p50_pct}% 대비 {ret_vs_median_pp}%p\n\n"
        "공개 기록 누적 {fwd_n}건: 하락 {fwd_fell_n}건 ({fwd_fell_share_pct}%)\n"
        "누락·오류 {fwd_missed_n}건 포함 전체 기록: {record_url}\n\n{disclaimer}"
    ),
}


class _Keep(dict):
    def __missing__(self, k):
        return "{" + k + "}"


def render(kind: str, v: dict, templates: dict | None = None) -> str:
    """Sales template if present and clean, else fallback. Disclaimer is always present."""
    v = {**v, "disclaimer": DISCLAIMER}
    for tpl in ((templates or {}).get(kind), FALLBACK[kind]):
        if not tpl:
            continue
        text = tpl.format_map(_Keep(v))
        if any(b in text for b in BANNED):
            log.warning("template %s has banned phrase, using fallback", kind)
            continue
        return text if DISCLAIMER in text else f"{text}\n\n{DISCLAIMER}"
    raise AssertionError("fallback template rendered banned phrase")


def load_templates() -> dict:
    try:
        return json.loads(TEMPLATES.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as e:
        log.warning("templates.json unreadable (%s), using fallback", e)
        return {}


def perp_candidates(t: str) -> list[str]:
    return [f"{t}USDT", f"1000{t}USDT", f"1000000{t}USDT", f"1M{t}USDT"]


def match_perp(t: str, symbols) -> str:
    return next((p for p in perp_candidates(t) if p in symbols), "")


def hist_vars(stats: dict, age_days: int | None) -> dict:
    b = next((k for k, lo, hi in (("<=30d", 0, 30), ("31-180d", 31, 180), (">180d", 181, 10**6))
              if age_days is not None and lo <= age_days <= hi), None)
    ab = stats["age_buckets"].get(b) or {}
    return {"hist_n": stats["n"], "hist_period": stats["period"], "hist_p10_pct": stats["ret7_p10_pct"],
            "hist_p50_pct": stats["ret7_p50_pct"], "hist_p90_pct": stats["ret7_p90_pct"],
            "hist_up30_n": stats["high7_ge30_n"], "hist_up30_share_pct": stats["high7_ge30_pct"],
            "hist_up_max_pct": stats["high7_max_pct"], "age_bucket": b or "-", "age_bucket_n": ab.get("n", "-"),
            "age_bucket_p50_pct": ab.get("ret7_p50_pct", "-")}


def _ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def _exists(url: str, params_for, sym_list) -> str:
    try:
        for s in sym_list:
            r = get(url, params_for(s), sleep=0.1, tries=2) or {}
            if (r.get("result") or {}).get("list") or r.get("data"):
                return s
        return "없음"
    except Exception as e:
        log.warning("perp check failed %s: %s", url, e)
        return "확인 실패"


def binance_perp(t: str, at: datetime) -> tuple[str, datetime | None]:
    """Binance USDT-M perp for t onboarded before `at`: ('', None) if absent. Raises if the API fails."""
    info = {s["symbol"]: s for s in get(f"{FAPI}/exchangeInfo", tries=3)["symbols"]
            if s.get("contractType") == "PERPETUAL" and s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"}
    sym = match_perp(t, info)
    onboard = datetime.fromtimestamp(info[sym]["onboardDate"] / 1000, tz=timezone.utc) if sym else None
    return (sym, onboard) if sym and onboard < at else ("", None)


def snapshot(t: str, at: datetime) -> dict:
    """Public market facts for ticker t at alert time `at`. binance_error = unknown (not absent)."""
    snap: dict = {"binance_symbol": ""}
    try:
        sym, onboard = binance_perp(t, at)
        if sym:
            snap.update(binance_symbol=sym, perp_age_days=(at - onboard).days)
            tk = get(f"{FAPI}/ticker/24hr", {"symbol": sym}, tries=3)
            pi = get(f"{FAPI}/premiumIndex", {"symbol": sym}, tries=3)
            snap.update(quote_volume_musd=round(float(tk["quoteVolume"]) / 1e6, 1),
                        funding_pct=round(float(pi["lastFundingRate"]) * 100, 4))
    except Exception as e:
        log.warning("binance lookup failed for %s: %s", t, e)
        snap["binance_error"] = str(e)[:200]
    c = perp_candidates(t)
    snap["bybit"] = _exists("https://api.bybit.com/v5/market/tickers", lambda s: {"category": "linear", "symbol": s}, c)
    snap["bitget"] = _exists("https://api.bitget.com/api/v2/mix/market/ticker",
                             lambda s: {"productType": "USDT-FUTURES", "symbol": s}, c)
    return snap


def fetch_listing_notices() -> list[tuple[str, str, str, str]]:
    d = get(NOTICE_URL, {"os": "web", "page": 1, "per_page": 20, "category": "trade"}, tries=3)
    notices = ((d or {}).get("data") or {}).get("notices")
    if notices is None:
        raise RuntimeError("notice API returned no data")
    return [(str(n["id"]), n.get("first_listed_at") or n.get("listed_at") or "", t, n["title"])
            for n in notices if LISTING.search(n["title"]) and "KRW" in n["title"]
            for t in TICKER.findall(n["title"]) if t != "KRW"]


def fetch_krw_markets() -> set[str]:
    return {m["market"][4:] for m in get("https://api.upbit.com/v1/market/all", tries=3) if m["market"].startswith("KRW-")}


def seven_day(sym: str, d0: date) -> dict | None:
    """Binance perp price change open(D+1) -> open(D+8) UTC days and max high D+1..D+7 (same as the frozen stats)."""
    e, x = d0 + timedelta(1), d0 + timedelta(8)
    k = get(f"{FAPI}/klines", {"symbol": sym, "interval": "1d", "startTime": _ms(e), "limit": 8}, tries=3) or []
    bars = {datetime.fromtimestamp(r[0] / 1000, tz=timezone.utc).date(): (float(r[1]), float(r[2])) for r in k}
    if e not in bars or x not in bars:
        return None
    p0 = bars[e][0]
    hi = max(bars[e + timedelta(i)][1] for i in range(7) if e + timedelta(i) in bars)
    raw = (bars[x][0] / p0 - 1) * 100
    return {"ret_7d_pct": round(raw, 1), "ret_7d_raw": raw, "high_7d_pct": round((hi / p0 - 1) * 100, 1),
            "price_source": f"Binance {sym}", "entry_date": str(e), "exit_date": str(x)}


def read_records() -> list[dict]:
    if not RECORD.exists():
        return []
    with open(RECORD, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_record(rec: dict) -> None:
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    rec = {"sent_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **rec}
    with open(RECORD, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def deliver(kind: str, text: str, rec: dict, dry: bool | None = None) -> None:
    dry = DRY_RUN if dry is None else dry
    sent = False
    if dry:
        log.info("[DRY_RUN %s]\n%s", kind, text)
    else:
        sent = TelegramNotifier(os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("LISTING_ALERT_CHAT_ID", "")).send(text)
    append_record({**rec, "kind": kind, "message": text,
                   "message_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "dry_run": dry, "sent": sent})


def kst_label(s: str) -> str:
    return datetime.fromisoformat(s).astimezone(KST).strftime("%Y-%m-%d %H:%M")


def _mine(records: list[dict], *kinds: str, dry: bool | None = None) -> list[dict]:
    dry = DRY_RUN if dry is None else dry
    return [r for r in records if r.get("kind") in kinds and r.get("dry_run") == dry]


def build_alert(nid: str, at_kst: str, t: str, title: str, stats: dict, templates: dict,
                snap: dict | None = None, alert_id: int | str = 1):
    at = datetime.fromisoformat(at_kst)
    snap = snap if snap is not None else snapshot(t, at.astimezone(timezone.utc))
    d0 = at.astimezone(KST).date()
    url = f"https://upbit.com/service_center/notice?id={nid}" if nid.isdigit() else "https://upbit.com/exchange"
    v = {"alert_id": alert_id, "ticker": t, "notice_title": title, "notice_time_kst": kst_label(at_kst), "notice_url": url,
         "perp_binance": snap.get("binance_symbol") or ("확인 실패" if snap.get("binance_error") else "없음"),
         "perp_bybit": snap.get("bybit", "-"),
         "perp_bitget": snap.get("bitget", "-"), "perp_age_days": snap.get("perp_age_days", "-"),
         "quote_volume_24h": vol_band(snap.get("quote_volume_musd")),
         "funding_rate_pct": funding_sign(snap.get("funding_pct")), "funding_source": "Binance 직전 정산",
         **hist_vars(stats, snap.get("perp_age_days"))}
    text = render("alert" if _eligible(snap) else "alert_no_perp", v, templates)
    rec = {"alert_id": alert_id, "ticker": t, "notice_id": nid, "title": title, "notice_at_kst": at_kst,
           "d0_kst": str(d0), "followup_due_utc": f"{d0 + timedelta(8)}T00:10:00+00:00", "snapshot": snap}
    return text, rec


def vol_band(musd) -> str:
    """Exchange data is shown as bands/signs, not raw feed values (docs/legal/upbit-listing-alert/issues.md)."""
    if musd is None:
        return "-"
    for hi, label in ((1, "100만 달러 미만"), (10, "100만~1천만 달러"), (100, "1천만~1억 달러")):
        if musd < hi:
            return label
    return "1억 달러 이상"


def funding_sign(pct) -> str:
    if pct is None or pct == "-":
        return "-"
    return "양(+)" if float(pct) > 0 else "음(−)" if float(pct) < 0 else "0"


def _eligible(snap: dict) -> bool:
    """Binance perp known, or lookup failed (unknown != absent: rechecked at follow-up)."""
    return bool(snap.get("binance_symbol") or snap.get("binance_error"))


def _raw(res: dict) -> float:
    return res.get("ret_7d_raw", res["ret_7d_pct"])


def followup_vars(alert: dict, res: dict | None, records: list[dict], stats: dict, dry: bool | None = None) -> dict:
    fus = _mine(records, "followup", dry=dry)
    fwd = [_raw(r["result"]) for r in fus if r.get("result")]
    missed = (len(_mine(records, "alert_error", dry=dry)) + sum(not r.get("result") for r in fus)
              + sum(r.get("source") == "upbit_notices" for r in _mine(records, "source_down", dry=dry)))
    if res:
        fwd.append(_raw(res))
    else:
        missed += 1
    fell = sum(r < 0 for r in fwd)
    p50 = stats["ret7_p50_pct"]
    sent = alert.get("sent_at")
    return {"ret_7d_pct": "데이터 없음", "high_7d_pct": "-", "price_source": "-", "entry_date": "-", "exit_date": "-",
            **(res or {}), "alert_id": alert.get("alert_id", "-"), "ticker": alert["ticker"],
            "alert_sent_kst": kst_label(sent) if sent else "-", "hist_p50_pct": p50,
            "ret_vs_median_pp": f"{res['ret_7d_pct'] - p50:+.1f}" if res else "-",
            "fwd_n": len(fwd), "fwd_fell_n": fell, "fwd_fell_share_pct": round(fell / len(fwd) * 100) if fwd else "-",
            "fwd_p50_pct": round(statistics.median(fwd), 1) if fwd else "-", "fwd_missed_n": missed, "record_url": RECORD_URL}


def due_followups(records: list[dict], now: datetime) -> list[dict]:
    """Eligible alerts (no-perp alerts are outside the sample: recorded only) whose D+8 has passed."""
    done = {(r["notice_id"], r["ticker"]) for r in records if r.get("kind") in ("followup", "followup_skipped")}
    return [r for r in records if r.get("kind") == "alert" and _eligible(r["snapshot"])
            and (r["notice_id"], r["ticker"]) not in done and datetime.fromisoformat(r["followup_due_utc"]) <= now]


def run_followups(stats: dict, templates: dict) -> None:
    now = datetime.now(timezone.utc)
    records = read_records()
    for a in due_followups(records, now):
        dry = DRY_RUN or a.get("dry_run", True) or not a.get("sent")  # only publicly sent alerts get public follow-ups
        try:
            sym = a["snapshot"].get("binance_symbol") or binance_perp(a["ticker"], datetime.fromisoformat(a["notice_at_kst"]))[0]
            if not sym:
                append_record({"kind": "followup_skipped", "ticker": a["ticker"], "notice_id": a["notice_id"],
                               "reason": "no Binance perp before notice (rechecked)", "dry_run": dry})
                continue
            res = seven_day(sym, date.fromisoformat(a["d0_kst"]))
        except Exception as e:
            log.warning("follow-up fetch failed %s: %s", a["ticker"], e)
            res = None
        if res is None and now < datetime.fromisoformat(a["followup_due_utc"]) + timedelta(days=7):
            continue  # retry next poll; give up (record "데이터 없음") after 7 more days
        text = render("followup", followup_vars(a, res, records, stats, dry), templates)
        deliver("followup", text, {"ticker": a["ticker"], "notice_id": a["notice_id"], "result": res}, dry)
        records = read_records()


def _source(state: dict, name: str, fn):
    """Call fn; record one line when a source goes down and one when it recovers (no per-poll spam)."""
    down = state.setdefault("down", {})
    try:
        out = fn()
    except Exception as e:
        log.warning("%s failed: %s", name, e)
        if not down.get(name):
            append_record({"kind": "source_down", "source": name, "error": str(e)[:300], "dry_run": DRY_RUN})
            down[name] = True
        return None
    if down.pop(name, False):
        append_record({"kind": "source_recovered", "source": name, "dry_run": DRY_RUN})
    return out


def new_listings(state: dict, notices, krw: set | None, now_kst: str) -> list[tuple[str, str, str, str]]:
    """Dedupe by notice id+ticker and by ticker; KRW market diff as fallback. Mutates state."""
    seen, tickers, out = set(state.get("seen", [])), set(state.get("tickers", [])), []
    for nid, at, t, title in notices or []:
        if f"{nid}:{t}" in seen:
            continue
        seen.add(f"{nid}:{t}")
        if t not in tickers:
            tickers.add(t)
            out.append((nid, at, t, title))
    if krw is not None:
        prev = set(state.get("krw_markets", []))
        if prev:
            for t in sorted(krw - prev - tickers):
                tickers.add(t)
                out.append((f"market:KRW-{t}", now_kst, t, f"업비트 KRW-{t} 마켓 신규 감지 (공지 미확인)"))
        state["krw_markets"] = sorted(krw)
    state["seen"], state["tickers"] = sorted(seen), sorted(tickers)
    return out


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE)


def run_once() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    boot = not (state.get("bootstrapped") or "seen" in state)
    # the jsonl is the source of truth: alerts recorded before a crash (state not yet saved) are not resent
    done = [r for r in read_records() if r.get("kind") in ("alert", "alert_error")]
    state["seen"] = sorted(set(state.get("seen", [])) | {f"{r['notice_id']}:{r['ticker']}" for r in done})
    state["tickers"] = sorted(set(state.get("tickers", [])) | {r["ticker"] for r in done})
    stats, templates = json.loads(STATS.read_text(encoding="utf-8")), load_templates()
    notices = _source(state, "upbit_notices", fetch_listing_notices)
    if boot and notices is None:
        return save_state({"down": state["down"]})  # keep the down flag; bootstrap needs the notice list or old notices would alert
    krw = _source(state, "upbit_market_all", fetch_krw_markets)
    new = new_listings(state, notices, krw, datetime.now(KST).isoformat(timespec="seconds"))
    if boot:
        append_record({"kind": "bootstrap", "skipped": [f"{n[0]}:{n[2]}" for n in new], "dry_run": DRY_RUN})
        state["bootstrapped"], new = True, []
    if new and DELAY_MIN:
        # ponytail: blocking sleep is fine at ~5 listings/month; a pending queue would be needed if polls must stay live.
        time.sleep(DELAY_MIN * 60)
    for nid, at, t, title in new:
        try:
            alert_id = len(_mine(read_records(), "alert")) + 1
            text, rec = build_alert(nid, at, t, title, stats, templates, alert_id=alert_id)
            deliver("alert", text, rec)
        except Exception as e:
            log.exception("alert failed %s", t)
            append_record({"kind": "alert_error", "ticker": t, "notice_id": nid, "error": str(e)[:300], "dry_run": DRY_RUN})
    save_state(state)
    run_followups(stats, templates)


def replay(t: str, at_kst: str) -> None:
    stats, templates = json.loads(STATS.read_text(encoding="utf-8")), load_templates()
    text, rec = build_alert("replay", at_kst, t, f"{t} (replay)", stats, templates, alert_id="R")
    print(text, "\n---\nsnapshot:", json.dumps(rec["snapshot"], ensure_ascii=False))
    sym = rec["snapshot"].get("binance_symbol")
    if sym and due_followups([rec | {"kind": "alert"}], datetime.now(timezone.utc)):
        res = seven_day(sym, date.fromisoformat(rec["d0_kst"]))
        print("---\n" + render("followup", followup_vars(rec, res, read_records(), stats), templates))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--replay", nargs=2, metavar=("TICKER", "NOTICE_TIME_ISO"))
    a = p.parse_args()
    if a.replay:
        return replay(a.replay[0].upper(), a.replay[1])
    if not DRY_RUN and not (os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("LISTING_ALERT_CHAT_ID")):
        log.warning("LIVE mode but TELEGRAM_BOT_TOKEN/LISTING_ALERT_CHAT_ID missing: messages will be recorded as sent=false")
    log.info("listing alert start dry_run=%s poll=%sm root=%s", DRY_RUN, POLL_MIN, ROOT)
    while True:
        try:
            run_once()
        except Exception:
            log.exception("poll failed")
        if a.once:
            return
        time.sleep(POLL_MIN * 60)


if __name__ == "__main__":
    main()
