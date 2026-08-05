#!/usr/bin/env python3
"""Strategy Audit Team — falsification-first gate.

Compares a candidate strategy JSON against a baseline on frozen windows.
Prefers REJECT/HOLD. Never recommends trades. Toolkit stdout metrics only.

Usage:
  python3 scripts/strategy_audit.py \\
    --candidate strategies/foo.json \\
    --baseline strategies/krw-btc-1h-ema-adx23-m5-v3.json \\
    --n-trials 4470 \\
    --out reports/audit/foo-vs-v3.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

DEFAULT_POLICY = ROOT / "reports" / "review-state" / "audit-policy.json"


def run_bt(strategy: Path, start: str, end: str) -> dict:
    e = "2026-07-26" if end > "2026-07-26" else end
    csv_path = run_backtest(strategy, start, e)
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_perf = False
    raw: dict[str, str] = {}
    for line in lines:
        if line.startswith("# section: performance"):
            in_perf = True
            continue
        if in_perf and line.startswith("# section:"):
            break
        if not in_perf or line.startswith("metric") or not line.strip():
            continue
        k, v = line.split(",", 1)
        raw[k] = v

    def num(key: str) -> float | None:
        v = raw.get(key)
        if v is None or v.startswith("N/A"):
            return None
        try:
            return float(v)
        except ValueError:
            return None

    trades = num("trades")
    return {
        "total_return_pct": num("total_return_pct"),
        "benchmark_pct": num("benchmark_pct"),
        "mdd_pct": num("mdd_pct"),
        "trades": int(trades) if trades is not None else None,
        "raw_ok": "total_return_pct" in raw,
    }


def complexity(strategy_path: Path) -> dict:
    obj = json.loads(strategy_path.read_text())
    buy = obj.get("buy", {})
    n_buy = len(buy.get("conditions", [])) if isinstance(buy, dict) else 0
    n_ind = len(obj.get("indicators", []))
    return {
        "buy_conditions": n_buy,
        "indicators": n_ind,
        "stop_loss": obj.get("stop_loss"),
        "take_profit": obj.get("take_profit"),
        "timeframe": obj.get("timeframe"),
    }


def gate_eval(policy: dict, cand: dict, base: dict, cx: dict, n_trials: int) -> list[dict]:
    gates = policy["gates"]
    results = []

    def win(key: str) -> dict:
        return cand["windows"][key], base["windows"][key]

    # G1
    g = gates["G1_min_trades_primary"]
    c_w, _ = win(g["window_key"])
    trades = c_w.get("trades") or 0
    ok = trades >= g["min_trades"]
    results.append({
        "id": "G1",
        "name": "min_trades_primary",
        "pass": ok,
        "detail": f"primary trades={trades} min={g['min_trades']}",
        "severity": "Too few trades — result may be luck / untradeable sparsity" if not ok else None,
    })

    # G2 holdout
    g = gates["G2_holdout_not_collapse"]
    c_w, b_w = win(g["window_key"])
    c_ret, b_ret = c_w["total_return_pct"], b_w["total_return_pct"]
    under = (b_ret - c_ret) if (c_ret is not None and b_ret is not None) else 999
    ok = under <= g["max_underperform_pp_vs_baseline"]
    results.append({
        "id": "G2",
        "name": "holdout_not_collapse",
        "pass": ok,
        "detail": f"holdout cand={c_ret}% base={b_ret}% underperform={under:.2f}pp max={g['max_underperform_pp_vs_baseline']}",
        "critique": "Holdout collapse suggests in-sample overfitting" if not ok else None,
    })

    # G3 early oos
    g = gates["G3_early_oos"]
    c_w, b_w = win(g["window_key"])
    c_ret, b_ret = c_w["total_return_pct"], b_w["total_return_pct"]
    under = (b_ret - c_ret) if (c_ret is not None and b_ret is not None) else 999
    ok = under <= g["max_underperform_pp_vs_baseline"]
    results.append({
        "id": "G3",
        "name": "early_oos",
        "pass": ok,
        "detail": f"early_oos cand={c_ret}% base={b_ret}% underperform={under:.2f}pp max={g['max_underperform_pp_vs_baseline']}",
        "critique": "Early OOS weak vs baseline — recent window may be curve-fit" if not ok else None,
    })

    # G4 shallow bear
    g = gates["G4_no_shallow_bear_regression"]
    c_w, b_w = win(g["window_key"])
    c_ret, b_ret = c_w["total_return_pct"], b_w["total_return_pct"]
    ok = c_ret is not None and b_ret is not None and c_ret >= b_ret
    results.append({
        "id": "G4",
        "name": "no_shallow_bear_regression",
        "pass": ok,
        "detail": f"stress_shallow_bear cand={c_ret}% base={b_ret}%",
        "critique": "Regressed on known shallow-bear failure mode" if not ok else None,
    })

    # G5 complexity tax
    g = gates["G5_complexity_tax"]
    extra_cond = max(0, cx["buy_conditions"] - g["buy_conditions_soft_cap"])
    extra_ind = max(0, cx["indicators"] - g["indicators_soft_cap"])
    tax = extra_cond * g["extra_edge_pp_per_extra_condition"] + extra_ind * g["extra_edge_pp_per_extra_indicator"]
    c_p, b_p = win("primary")
    edge = (c_p["total_return_pct"] - b_p["total_return_pct"]) if c_p["total_return_pct"] is not None else -999
    # Complexity tax only applies when more complex; if simpler/equal, pass if not collapsing primary badly
    if tax <= 0:
        ok = True
        detail = f"no complexity tax (buy={cx['buy_conditions']} ind={cx['indicators']})"
        critique = None
    else:
        ok = edge >= tax
        detail = f"primary edge vs base={edge:.2f}pp required_tax={tax:.2f}pp (extra_cond={extra_cond} extra_ind={extra_ind})"
        critique = "Extra filters without enough primary edge — complexity not justified" if not ok else None
    results.append({"id": "G5", "name": "complexity_tax", "pass": ok, "detail": detail, "critique": critique})

    # G6 MDD
    g = gates["G6_mdd_guard"]
    c_w, b_w = win(g["window_key"])
    # MDD printed as negative or positive magnitude depending on tool; compare absolute
    c_mdd = abs(c_w.get("mdd_pct") or 0)
    b_mdd = abs(b_w.get("mdd_pct") or 0)
    worse = c_mdd - b_mdd
    ok = worse <= g["max_mdd_worse_pp_vs_baseline"]
    results.append({
        "id": "G6",
        "name": "mdd_guard",
        "pass": ok,
        "detail": f"primary |MDD| cand={c_mdd}% base={b_mdd}% worse={worse:.2f}pp max={g['max_mdd_worse_pp_vs_baseline']}",
        "critique": "Primary drawdown materially worse than baseline" if not ok else None,
    })

    # G8 multiple testing
    g = gates["G8_multiple_testing_suspicion"]
    if n_trials >= g["n_trials_threshold"]:
        tight = g["tight_underperform_pp"]
        checks = []
        for key in ("holdout", "early_oos"):
            c_w, b_w = win(key)
            under = (b_w["total_return_pct"] - c_w["total_return_pct"])
            checks.append(under <= tight)
        ok = all(checks)
        results.append({
            "id": "G8",
            "name": "multiple_testing_suspicion",
            "pass": ok,
            "detail": f"n_trials={n_trials}>= {g['n_trials_threshold']}; tight underperform max={tight}pp on holdout+early_oos; checks={checks}",
            "critique": "Large sweep → higher bar failed on holdout/early (selection bias risk)" if not ok else None,
        })
    else:
        results.append({
            "id": "G8",
            "name": "multiple_testing_suspicion",
            "pass": True,
            "detail": f"n_trials={n_trials} < threshold {g['n_trials_threshold']} — tight bar skipped",
            "critique": None,
        })

    return results


def verdict_from(policy: dict, gate_results: list[dict]) -> dict:
    by = {g["id"]: g for g in gate_results}
    hard = policy["promotion_rules"]["hard_reject_if_any_fail"]
    if any(not by[g]["pass"] for g in hard if g in by):
        return {"verdict": "REJECT", "reason": "Hard reject gate failed (G1 and/or G4)"}

    def all_pass(ids):
        return all(by[i]["pass"] for i in ids if i in by)

    live_ids = policy["promotion_rules"]["to_LIVE_OK_WITH_HUMAN"]
    cand_ids = policy["promotion_rules"]["to_PROMOTE_CANDIDATE"]

    if all_pass(live_ids):
        return {
            "verdict": "LIVE_OK_WITH_HUMAN",
            "reason": "All LIVE audit gates passed — human may deploy; automation must NOT auto-deploy",
        }
    if all_pass(cand_ids):
        return {
            "verdict": "PROMOTE_CANDIDATE",
            "reason": "Research/PR candidate OK; missing LIVE bar (often G8). Do not claim LIVE-ready.",
        }
    failed = [g["id"] for g in gate_results if not g["pass"]]
    if failed:
        # soft research hold if only complexity/mdd etc.
        if set(failed) <= {"G5", "G6", "G8", "G2", "G3"}:
            return {"verdict": "HOLD", "reason": f"Interesting but not promotable; failed {failed}"}
        return {"verdict": "REJECT", "reason": f"Failed gates {failed}"}
    return {"verdict": "HOLD", "reason": "No clear promotion path"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Falsification-first strategy audit")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--policy", default=str(DEFAULT_POLICY))
    ap.add_argument("--n-trials", type=int, default=0, help="Size of search that produced candidate")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    policy = json.loads(Path(args.policy).read_text())
    cand_path = Path(args.candidate)
    base_path = Path(args.baseline)
    if not cand_path.is_absolute():
        cand_path = ROOT / cand_path
    if not base_path.is_absolute():
        base_path = ROOT / base_path

    windows = policy["windows"]
    cand_wins = {}
    base_wins = {}
    print("Audit Team: running critical windows (toolkit metrics only)...", flush=True)
    for key, meta in windows.items():
        print(f"  window {key}: {meta['start']} .. {meta['end']}", flush=True)
        cand_wins[key] = run_bt(cand_path, meta["start"], meta["end"])
        base_wins[key] = run_bt(base_path, meta["start"], meta["end"])
        print(
            f"    cand ret={cand_wins[key]['total_return_pct']} n={cand_wins[key]['trades']} | "
            f"base ret={base_wins[key]['total_return_pct']} n={base_wins[key]['trades']}",
            flush=True,
        )

    cx = complexity(cand_path)
    gate_results = gate_eval(
        policy,
        {"windows": cand_wins},
        {"windows": base_wins},
        cx,
        args.n_trials,
    )
    decision = verdict_from(policy, gate_results)

    critiques = [g["critique"] for g in gate_results if g.get("critique")]
    report = {
        "role": "audit_team",
        "stance": "critical / falsification-first",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candidate": str(cand_path.relative_to(ROOT)),
        "baseline": str(base_path.relative_to(ROOT)),
        "n_trials": args.n_trials,
        "complexity": cx,
        "windows": {
            k: {
                "meta": windows[k],
                "candidate": cand_wins[k],
                "baseline": base_wins[k],
            }
            for k in windows
        },
        "gates": gate_results,
        "decision": decision,
        "critiques": critiques,
        "forbidden_claims": policy["gates"]["G7_benchmark_honesty"]["forbid_claim_keys"],
        "human_required_for_live": True,
        "disclaimer": [
            "Audit uses historical backtests only; future results are not guaranteed.",
            "Slippage / liquidity / partial fills are not modeled.",
            "This is not investment advice and does not recommend live trading.",
        ],
    }

    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    print("\n=== AUDIT DECISION ===", flush=True)
    print(decision["verdict"], "-", decision["reason"], flush=True)
    for g in gate_results:
        mark = "PASS" if g["pass"] else "FAIL"
        print(f"  [{mark}] {g['id']} {g['name']}: {g['detail']}", flush=True)
    print(f"\nWrote {out}", flush=True)

    # exit code: 0 always for report writing; automation should read verdict field
    # Use 2 for REJECT to make CI/automation easy
    if decision["verdict"] == "REJECT":
        return 2
    if decision["verdict"] == "HOLD":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
