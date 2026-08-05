"""Fee stress + LIVE promotion review for ledger candidates.

Runs when a PF-pass candidate lacks promote_review. Never writes Policy C / LIVE.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_tick_path = Path(__file__).with_name("auto_slot_fill_tick.py")
_spec = importlib.util.spec_from_file_location("auto_slot_fill_tick", _tick_path)
tick = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(tick)

# Quarters for fragility (cpp only — fast)
QUARTERS = (
    ("q1", "2025-09-01", "2025-11-15"),
    ("q2", "2025-11-15", "2026-02-01"),
    ("q3", "2026-02-01", "2026-04-15"),
    ("q4", "2026-04-15", "2026-08-05"),
)

# Side fees as fractions (0.0010 = 10 bps/side)
FEE_LADDER = (0.0, 0.0006, 0.0010, 0.0012)
# FT only on base + 10bps (slow)
FT_FEES = (0.0006, 0.0010)


def _ok_half(w: dict, nmin: int = 20, pfmin: float = 1.2) -> bool:
    return (w.get("trades") or 0) >= nmin and (w.get("profit_factor") or 0) >= pfmin


def _both(h1: dict, h2: dict, nmin: int = 20, pfmin: float = 1.2) -> bool:
    return _ok_half(h1, nmin, pfmin) and _ok_half(h2, nmin, pfmin)


def pending_candidate(ledger: dict) -> dict | None:
    for c in ledger.get("candidates") or []:
        if c.get("promote_review"):
            continue
        if c.get("status") in ("REJECTED", "FRAGILE"):
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
        fee_cpp[str(fee)] = {
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
            fee_ft[str(fee)] = {
                "h1": h1,
                "h2": h2,
                "pass_pf12": _both(h1, h2, nmin, pfmin),
            }

    quarters = {}
    q_ge1 = 0
    for name, start, end in QUARTERS:
        e = {**exp, "fee": 0.0006}
        w = tick.cpp_window(e, start, end)
        quarters[name] = w
        if (w.get("profit_factor") or 0) >= 1.0 and (w.get("trades") or 0) >= 5:
            q_ge1 += 1

    # Neighbor sensitivity (cpp): ADX ±3 and exit stretch
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
        e = {**exp, "adx_min": adx, "sl": sl, "tp": tp, "fee": 0.0006}
        h1 = tick.cpp_window(e, tick.WINDOWS[0][1], tick.WINDOWS[0][2])
        h2 = tick.cpp_window(e, tick.WINDOWS[1][1], tick.WINDOWS[1][2])
        ok = _both(h1, h2, nmin, pfmin)
        neighbors[tag] = {"adx": adx, "sl": sl, "tp": tp, "h1": h1, "h2": h2, "pass_pf12": ok}
        if ok:
            neigh_pass += 1

    base_cpp = fee_cpp.get("0.0006", {})
    h2pf = (base_cpp.get("h2") or {}).get("profit_factor") or 0
    fragile: list[str] = []
    if h2pf < 1.25:
        fragile.append("h2 PF only marginally >=1.2")
    if fee_cpp.get("0.001", {}).get("pass_pf12") is False or fee_cpp.get("0.0010", {}).get("pass_pf12") is False:
        fragile.append("fails at 10bps/side fee (cpp)")
    if fee_ft.get("0.001", {}).get("pass_pf12") is False or fee_ft.get("0.0010", {}).get("pass_pf12") is False:
        fragile.append("fails at 10bps/side fee (ft)")
    if fee_cpp.get("0.0012", {}).get("pass_pf12") is False:
        fragile.append("fails at 12bps/side fee (cpp)")

    base_pass = bool(base_cpp.get("pass_pf12"))
    ft_base_pass = fee_ft.get("0.0006", {}).get("pass_pf12")
    if fee_ft and ft_base_pass is False:
        base_pass = False
        fragile.append("FT fixed-stake fails base 6bps")

    fee10_ok = (
        fee_ft.get("0.0010", {}).get("pass_pf12")
        if fee_ft
        else fee_cpp.get("0.0010", {}).get("pass_pf12")
    )

    # Status ladder — human still required for any LIVE; automation never mounts.
    if not base_pass:
        status = "REJECTED"
    elif q_ge1 >= 3 and neigh_pass >= 4 and fee10_ok:
        status = "LIVE_OK_WITH_HUMAN"
    elif q_ge1 >= 3 and neigh_pass >= 3 and fee10_ok:
        status = "PROMOTE_CANDIDATE"
    elif base_pass and q_ge1 >= 2 and neigh_pass >= 2:
        status = "RESEARCH_KEEP"
    else:
        status = "FRAGILE"

    review = {
        "at": tick.utc_now(),
        "fee_stress_cpp": fee_cpp,
        "fee_stress_ft": fee_ft,
        "quarters_cpp": quarters,
        "quarters_pf_ge_1": q_ge1,
        "neighbors_cpp": neighbors,
        "neighbor_pass": f"{neigh_pass}/{len(neigh_specs)}",
        "fragile": fragile,
        "fee10_pass": bool(fee10_ok),
        "status": status,
        "promote_auto": False,
        "note": "LIVE mount requires human; automation must not write Policy C / sleeves.",
    }
    return review


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
        "fee10_pass": review["fee10_pass"],
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
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
