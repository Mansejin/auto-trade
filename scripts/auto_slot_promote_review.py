"""Fee stress + LIVE promotion review for ledger candidates.

Runs when a PF-pass candidate lacks promote_review (or outdated gate_version).
Never writes Policy C / LIVE.

Fee model (Bitget USDT-M futures, default retail):
  maker ~2bps / taker ~6bps per side → backtests use base fee=0.0006 (taker).
  Stress gate = 8bps/side (~taker + small slip cushion). 10/12bps stay informational.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_tick_path = Path(__file__).with_name("auto_slot_fill_tick.py")
_spec = importlib.util.spec_from_file_location("auto_slot_fill_tick", _tick_path)
tick = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(tick)

GATE_VERSION = "base6_stress8_v1"
BASE_FEE = 0.0006
STRESS_FEE = 0.0008  # 8 bps/side — LIVE gate
# cpp ladder: base + stress + info (10/12)
FEE_LADDER = (0.0, BASE_FEE, STRESS_FEE, 0.0010, 0.0012)
FT_FEES = (BASE_FEE, STRESS_FEE)

QUARTERS = (
    ("q1", "2025-09-01", "2025-11-15"),
    ("q2", "2025-11-15", "2026-02-01"),
    ("q3", "2026-02-01", "2026-04-15"),
    ("q4", "2026-04-15", "2026-08-05"),
)


def _fee_key(fee: float) -> str:
    return f"{fee:.4f}".rstrip("0").rstrip(".") if fee else "0.0"


def _ok_half(w: dict, nmin: int = 20, pfmin: float = 1.2) -> bool:
    return (w.get("trades") or 0) >= nmin and (w.get("profit_factor") or 0) >= pfmin


def _both(h1: dict, h2: dict, nmin: int = 20, pfmin: float = 1.2) -> bool:
    return _ok_half(h1, nmin, pfmin) and _ok_half(h2, nmin, pfmin)


def pending_candidate(ledger: dict) -> dict | None:
    for c in ledger.get("candidates") or []:
        if c.get("status") in ("REJECTED",):
            continue
        pr = c.get("promote_review")
        if pr and pr.get("gate_version") == GATE_VERSION:
            continue
        return c
    return None


def review_candidate(cand: dict, crit: dict | None = None) -> dict:
    """Fee stress (cpp ladder + FT spot) + neighbor/quarter gates → verdict."""
    crit = crit or {"min_pf": 1.2, "min_trades": 20}
    nmin = int(crit.get("min_trades", 20))
    pfmin = float(crit.get("min_pf", 1.2))
    exp = dict(cand["exp"])
    tick.ensure_cpp()
    tick.ensure_data("BTC_USDT_USDT", exp.get("tf", "5m"))

    fee_cpp: dict = {}
    for fee in FEE_LADDER:
        e = {**exp, "fee": fee}
        h1 = tick.cpp_window(e, tick.WINDOWS[0][1], tick.WINDOWS[0][2])
        h2 = tick.cpp_window(e, tick.WINDOWS[1][1], tick.WINDOWS[1][2])
        fee_cpp[_fee_key(fee)] = {
            "h1": h1,
            "h2": h2,
            "pass_pf12": _both(h1, h2, nmin, pfmin),
        }

    fee_ft: dict = {}
    if cand.get("slot", "").startswith("scalp_") and exp.get("family") == "trend_short_neighbor":
        for fee in FT_FEES:
            e = {**exp, "fee": fee}
            h1 = tick.ft_window(tick.WINDOWS[0][1], tick.WINDOWS[0][2], e)
            h2 = tick.ft_window(tick.WINDOWS[1][1], tick.WINDOWS[1][2], e)
            fee_ft[_fee_key(fee)] = {
                "h1": h1,
                "h2": h2,
                "pass_pf12": _both(h1, h2, nmin, pfmin),
            }

    quarters = {}
    q_ge1 = 0
    for name, start, end in QUARTERS:
        e = {**exp, "fee": BASE_FEE}
        w = tick.cpp_window(e, start, end)
        quarters[name] = w
        if (w.get("profit_factor") or 0) >= 1.0 and (w.get("trades") or 0) >= 5:
            q_ge1 += 1

    base_adx = int(exp.get("adx_min", 15))
    neighbors = {}
    neigh_specs = [
        ("base", base_adx, exp["sl"], exp["tp"]),
        ("adx_m3", max(8, base_adx - 3), exp["sl"], exp["tp"]),
        ("adx_p3", base_adx + 3, exp["sl"], exp["tp"]),
        ("sl_tight", base_adx, round(exp["sl"] * 0.83, 4), round(exp["tp"] * 0.83, 4)),
        ("sl_wide", base_adx, round(exp["sl"] * 1.17, 4), round(exp["tp"] * 1.17, 4)),
        ("tp_wide", base_adx, exp["sl"], round(exp["tp"] * 1.33, 4)),
        ("tp_narrow", base_adx, exp["sl"], round(exp["tp"] * 0.67, 4)),
    ]
    neigh_pass = 0
    for tag, adx, sl, tp in neigh_specs:
        e = {**exp, "adx_min": adx, "sl": sl, "tp": tp, "fee": BASE_FEE}
        h1 = tick.cpp_window(e, tick.WINDOWS[0][1], tick.WINDOWS[0][2])
        h2 = tick.cpp_window(e, tick.WINDOWS[1][1], tick.WINDOWS[1][2])
        ok = _both(h1, h2, nmin, pfmin)
        neighbors[tag] = {"adx": adx, "sl": sl, "tp": tp, "h1": h1, "h2": h2, "pass_pf12": ok}
        if ok:
            neigh_pass += 1

    sk = _fee_key(STRESS_FEE)
    bk = _fee_key(BASE_FEE)
    base_cpp = fee_cpp.get(bk, {})
    h2pf = (base_cpp.get("h2") or {}).get("profit_factor") or 0
    fragile: list[str] = []
    if h2pf < 1.25:
        fragile.append("h2 PF only marginally >=1.2")
    if fee_cpp.get(sk, {}).get("pass_pf12") is False:
        fragile.append("fails at 8bps/side fee stress (cpp)")
    if fee_ft.get(sk, {}).get("pass_pf12") is False:
        fragile.append("fails at 8bps/side fee stress (ft)")
    # informational only
    if fee_cpp.get("0.001", {}).get("pass_pf12") is False:
        fragile.append("info: fails at 10bps/side (cpp)")
    if fee_cpp.get("0.0012", {}).get("pass_pf12") is False:
        fragile.append("info: fails at 12bps/side (cpp)")

    base_pass = bool(base_cpp.get("pass_pf12"))
    if fee_ft and fee_ft.get(bk, {}).get("pass_pf12") is False:
        base_pass = False
        fragile.append("FT fixed-stake fails base 6bps")

    stress_ok = (
        fee_ft.get(sk, {}).get("pass_pf12") if fee_ft else fee_cpp.get(sk, {}).get("pass_pf12")
    )

    if not base_pass:
        status = "REJECTED"
    elif q_ge1 >= 3 and neigh_pass >= 4 and stress_ok:
        status = "LIVE_OK_WITH_HUMAN"
    elif q_ge1 >= 3 and neigh_pass >= 3 and stress_ok:
        status = "PROMOTE_CANDIDATE"
    elif base_pass and q_ge1 >= 2 and neigh_pass >= 2:
        status = "RESEARCH_KEEP"
    else:
        status = "FRAGILE"

    return {
        "at": tick.utc_now(),
        "gate_version": GATE_VERSION,
        "base_fee": BASE_FEE,
        "stress_fee": STRESS_FEE,
        "fee_stress_cpp": fee_cpp,
        "fee_stress_ft": fee_ft,
        "quarters_cpp": quarters,
        "quarters_pf_ge_1": q_ge1,
        "neighbors_cpp": neighbors,
        "neighbor_pass": f"{neigh_pass}/{len(neigh_specs)}",
        "fragile": fragile,
        "fee_stress_pass": bool(stress_ok),
        "fee10_pass": bool(stress_ok),  # compat for older automation prompts
        "status": status,
        "promote_auto": False,
        "note": (
            "Base=Bitget taker 6bps; stress=8bps cushion. "
            "LIVE mount requires human; never write Policy C / sleeves."
        ),
    }


def review_next_pending(ledger: dict, slots_doc: dict | None = None) -> dict | None:
    cand = pending_candidate(ledger)
    if not cand:
        return None
    crit = {"min_pf": 1.2, "min_trades": 20}
    if slots_doc:
        for s in slots_doc.get("slots") or []:
            if s.get("id") == cand.get("slot"):
                crit = s.get("criteria") or crit
                break
    print(f"promote_review fp={cand.get('fingerprint')} slot={cand.get('slot')}", flush=True)
    review = review_candidate(cand, crit)
    cand["promote_review"] = review
    cand["status"] = review["status"]
    out = tick.OUT / "candidates" / f"{cand['slot']}-{cand['fingerprint']}.json"
    tick.save_json(out, cand)
    tick.save_json(tick.OUT / "promote" / f"{cand['fingerprint']}.json", review)
    return {
        "ok": True,
        "action": "promote_review",
        "slot": cand.get("slot"),
        "fingerprint": cand.get("fingerprint"),
        "status": review["status"],
        "gate_version": GATE_VERSION,
        "fee_stress_pass": review["fee_stress_pass"],
        "fee10_pass": review["fee_stress_pass"],
        "fragile": review["fragile"],
        "neighbor_pass": review["neighbor_pass"],
        "quarters_pf_ge_1": review["quarters_pf_ge_1"],
        "at": review["at"],
    }


def main() -> None:
    tick.OUT.mkdir(parents=True, exist_ok=True)
    ledger = tick.load_json(tick.LEDGER) if tick.LEDGER.exists() else {"candidates": []}
    slots = tick.load_json(tick.SLOTS) if tick.SLOTS.exists() else {}
    result = review_next_pending(ledger, slots)
    if not result:
        result = {"ok": True, "action": "idle", "reason": "no pending candidate review", "at": tick.utc_now()}
    else:
        ledger["last_tick"] = result
        tick.save_json(tick.LEDGER, ledger)
    import json

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
