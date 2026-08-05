"""Deep validation for Bitget BTC 5m swing short (di_cloud / SL3% / TP9%)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ft_bt_fast import ExitParams, FtGrid  # noqa: E402

FT = ROOT / "freqtrade-research"
CFG = (FT / "user_data" / "config.bitget-rsi-ichi-check.json").resolve()
STRAT = FT / "user_data" / "strategies" / "TrendShortV1.py"
OUT = ROOT / "reports" / "bitget-btc-short-swing-deep-20260805"
CPP = ROOT / "cpp-bt" / "build" / "cpp-bt.exe"
DATA = ROOT / "cpp-bt" / "data"

# Canonical HIT
BASE = dict(mode="di_cloud", adx_min=15, rsi_max=55, sl=-0.03, tp=0.09)

# Multi-window OOS (include original halves + quarters + full)
WINDOWS = [
    ("full", "20250901-20260805"),
    ("h1", "20250901-20260204"),
    ("h2", "20260204-20260805"),
    ("q1", "20250901-20251115"),
    ("q2", "20251115-20260201"),
    ("q3", "20260201-20260415"),
    ("q4", "20260415-20260805"),
]


def ensure_ft_config() -> None:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    cfg["entry_pricing"]["use_order_book"] = False
    cfg["exit_pricing"]["use_order_book"] = False
    cfg["stake_amount"] = 100
    cfg["dry_run_wallet"] = 1000
    cfg["export"] = "none"
    cfg["fee"] = 0.0006
    cfg["strategy"] = "TrendShortV1"
    CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def patch_strat(mode: str, adx: int, rsi: int, sl: float, tp: float) -> None:
    t = STRAT.read_text(encoding="utf-8")
    t = re.sub(r"stoploss = -0\.\d+", f"stoploss = {sl}", t, count=1)
    t = re.sub(r'minimal_roi = \{"0": 0\.\d+\}', f'minimal_roi = {{"0": {tp}}}', t, count=1)
    t = re.sub(r'entry_mode = "[^"]+"', f'entry_mode = "{mode}"', t, count=1)
    t = re.sub(r"adx_min = \d+", f"adx_min = {adx}", t, count=1)
    t = re.sub(r"rsi_max = \d+", f"rsi_max = {rsi}", t, count=1)
    STRAT.write_text(t, encoding="utf-8")


def ft_run(tr: str, mode: str, adx: int, rsi: int, sl: float, tp: float, fee: float = 0.0006) -> dict:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    cfg["fee"] = fee
    CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    patch_strat(mode, adx, rsi, sl, tp)
    p = subprocess.run(
        [
            str(FT / ".venv" / "Scripts" / "freqtrade.exe"),
            "backtesting",
            "--config",
            str(CFG),
            "--strategy",
            "TrendShortV1",
            "--timerange",
            tr,
            "--cache",
            "none",
            "--export",
            "none",
        ],
        cwd=FT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = (p.stdout or "") + "\n" + (p.stderr or "")
    text = text.replace("│", "|").replace("┃", "|")
    if "No trades made" in text or "Configuration error" in text:
        return {"trades": 0, "profit_factor": None, "profit_pct": None, "error": text[-400:]}
    out: dict = {}
    m = re.search(r"Total/Daily Avg Trades\s*\|\s*(\d+)", text)
    out["trades"] = int(m.group(1)) if m else 0
    m = re.search(r"Profit factor\s*\|\s*([0-9.]+|nan)", text)
    out["profit_factor"] = None if not m or m.group(1) == "nan" else float(m.group(1))
    m = re.search(r"Total profit %\s*\|\s*([+-]?[0-9.]+)%", text)
    out["profit_pct"] = float(m.group(1)) if m else None
    m = re.search(r"Max % of account underwater\s*\|\s*([0-9.]+)%", text)
    out["max_dd_pct"] = float(m.group(1)) if m else None
    return out


def write_cpp_strat(path: Path, mode: str, adx: int, rsi: int, sl: float, tp: float, fee: float) -> None:
    obj = {
        "name": "swing-deep",
        "side": "short",
        "symbols": ["BTC_USDT_USDT"],
        "timeframe": "5m",
        "fee": fee,
        "startup": 80,
        "entry": {
            "mode": mode,
            "rsi_period": 14,
            "adx_period": 14,
            "adx_min": adx,
            "rsi_max": rsi,
        },
        "exit": {
            "stoploss": sl,
            "take_profit": tp,
            "trailing": False,
            "trail_pos": 0.0,
            "trail_offset": 0.0,
        },
    }
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def cpp_run(start: str, end: str, mode: str, adx: int, rsi: int, sl: float, tp: float, fee: float) -> dict:
    strat = OUT / "_tmp_strat.json"
    write_cpp_strat(strat, mode, adx, rsi, sl, tp, fee)
    # dates YYYY-MM-DD
    s = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
    e = f"{end[:4]}-{end[4:6]}-{end[6:8]}"
    p = subprocess.run(
        [
            str(CPP),
            "run",
            "--strategy",
            str(strat),
            "--data",
            str(DATA),
            "--start",
            s,
            "--end",
            e,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = (p.stdout or "") + (p.stderr or "")
    m = re.search(r"trades=(\d+) pf=([0-9.]+) pnl_pct_sum=([+-]?[0-9.]+)", text)
    if not m:
        return {"trades": 0, "profit_factor": None, "profit_pct": None, "raw": text[-300:]}
    return {
        "trades": int(m.group(1)),
        "profit_factor": float(m.group(2)),
        "profit_pct": float(m.group(3)),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ensure_ft_config()
    report: dict = {"base": BASE, "engine": "FT fixed-stake100 + cpp-bt ftind"}

    # 1) Multi-window FT + cpp
    print("=== windows ===", flush=True)
    windows = {}
    for name, tr in WINDOWS:
        start, end = tr.split("-")
        ft = ft_run(tr, BASE["mode"], BASE["adx_min"], BASE["rsi_max"], BASE["sl"], BASE["tp"])
        cpp = cpp_run(start, end, BASE["mode"], BASE["adx_min"], BASE["rsi_max"], BASE["sl"], BASE["tp"], 0.0006)
        windows[name] = {"timerange": tr, "ft": ft, "cpp": cpp}
        print(
            f"  {name} FT pf={ft.get('profit_factor')} n={ft.get('trades')} dd={ft.get('max_dd_pct')} "
            f"| cpp pf={cpp.get('profit_factor')} n={cpp.get('trades')}",
            flush=True,
        )
    report["windows"] = windows

    # 2) Fee stress (FT, h1+h2)
    print("=== fee stress ===", flush=True)
    fees = {}
    for fee in (0.0, 0.0006, 0.0010, 0.0012):
        by = {}
        for name, tr in (("h1", "20250901-20260204"), ("h2", "20260204-20260805")):
            by[name] = ft_run(tr, BASE["mode"], BASE["adx_min"], BASE["rsi_max"], BASE["sl"], BASE["tp"], fee)
        ok = all((by[n].get("trades") or 0) >= 20 and (by[n].get("profit_factor") or 0) >= 1.2 for n in by)
        fees[str(fee)] = {"windows": by, "pass_pf12": ok}
        print(
            f"  fee={fee} h1={by['h1'].get('profit_factor')}/{by['h1'].get('trades')} "
            f"h2={by['h2'].get('profit_factor')}/{by['h2'].get('trades')} pass={ok}",
            flush=True,
        )
    report["fee_stress"] = fees

    # 3) Ablation (FT h1+h2)
    print("=== ablation ===", flush=True)
    ablations = {
        "base_di_cloud": ("di_cloud", 15, 55),
        "di_only": ("di_only", 15, 70),  # loose rsi
        "cloud_break": ("cloud_break", 15, 55),
        "di_cloud_adx25": ("di_cloud", 25, 55),
        "di_cloud_adx10": ("di_cloud", 10, 55),
    }
    abl = {}
    for tag, (mode, adx, rsi) in ablations.items():
        by = {}
        for name, tr in (("h1", "20250901-20260204"), ("h2", "20260204-20260805")):
            by[name] = ft_run(tr, mode, adx, rsi, BASE["sl"], BASE["tp"])
        abl[tag] = by
        print(
            f"  {tag} h1={by['h1'].get('profit_factor')}/{by['h1'].get('trades')} "
            f"h2={by['h2'].get('profit_factor')}/{by['h2'].get('trades')}",
            flush=True,
        )
    report["ablation"] = abl

    # 4) Sensitivity grid via cpp (fast): adx x sl x tp around base, both halves
    print("=== sensitivity cpp ===", flush=True)
    sens = []
    for adx in (10, 12, 15, 18, 20, 25):
        for sl, tp in (
            (-0.020, 0.060),
            (-0.025, 0.075),
            (-0.030, 0.090),
            (-0.035, 0.105),
            (-0.040, 0.120),
            (-0.030, 0.060),
            (-0.030, 0.120),
            (-0.020, 0.090),
        ):
            h1 = cpp_run("20250901", "20260204", "di_cloud", adx, 55, sl, tp, 0.0006)
            h2 = cpp_run("20260204", "20260805", "di_cloud", adx, 55, sl, tp, 0.0006)
            ok = (
                (h1.get("trades") or 0) >= 20
                and (h2.get("trades") or 0) >= 20
                and (h1.get("profit_factor") or 0) >= 1.2
                and (h2.get("profit_factor") or 0) >= 1.2
            )
            row = {
                "adx": adx,
                "sl": sl,
                "tp": tp,
                "h1": h1,
                "h2": h2,
                "min_pf": min(h1.get("profit_factor") or 0, h2.get("profit_factor") or 0),
                "pass_pf12": ok,
            }
            sens.append(row)
    sens.sort(key=lambda r: r["min_pf"], reverse=True)
    report["sensitivity_cpp"] = {"n": len(sens), "hits_pf12": [r for r in sens if r["pass_pf12"]], "top15": sens[:15]}
    print(f"  combos={len(sens)} pf12_hits={len(report['sensitivity_cpp']['hits_pf12'])}", flush=True)
    if sens:
        b = sens[0]
        print(f"  best minPF={b['min_pf']:.3f} adx={b['adx']} sl={b['sl']} tp={b['tp']}", flush=True)

    # 5) FT confirm top sensitivity neighbors of base
    print("=== FT confirm neighbors ===", flush=True)
    neighbors = [
        ("base", 15, -0.03, 0.09),
        ("adx12", 12, -0.03, 0.09),
        ("adx18", 18, -0.03, 0.09),
        ("sl25_tp75", 15, -0.025, 0.075),
        ("sl35_tp105", 15, -0.035, 0.105),
        ("sl30_tp60", 15, -0.03, 0.06),
        ("sl30_tp120", 15, -0.03, 0.12),
    ]
    neigh = {}
    for tag, adx, sl, tp in neighbors:
        by = {}
        for name, tr in (("h1", "20250901-20260204"), ("h2", "20260204-20260805")):
            by[name] = ft_run(tr, "di_cloud", adx, 55, sl, tp)
        ok = all((by[n].get("trades") or 0) >= 20 and (by[n].get("profit_factor") or 0) >= 1.2 for n in by)
        neigh[tag] = {"windows": by, "pass_pf12": ok, "adx": adx, "sl": sl, "tp": tp}
        print(
            f"  {tag} pass={ok} h1={by['h1'].get('profit_factor')}/{by['h1'].get('trades')} "
            f"h2={by['h2'].get('profit_factor')}/{by['h2'].get('trades')}",
            flush=True,
        )
    report["neighbors_ft"] = neigh

    # Verdict
    h1pf = windows["h1"]["ft"].get("profit_factor") or 0
    h2pf = windows["h2"]["ft"].get("profit_factor") or 0
    fee_pass = fees.get("0.0006", {}).get("pass_pf12")
    q_pfs = [(n, windows[n]["ft"].get("profit_factor")) for n in ("q1", "q2", "q3", "q4")]
    q_pos = sum(1 for _, pf in q_pfs if pf and pf >= 1.0)
    fragile = []
    if h2pf < 1.25:
        fragile.append("h2 PF only marginally >=1.2")
    if fees.get("0.001", {}).get("pass_pf12") is False:
        fragile.append("fails at 10bps/side fee")
    if abl["di_cloud_adx25"]["h2"].get("profit_factor") is not None and (
        abl["di_cloud_adx25"]["h2"].get("profit_factor") or 0
    ) < 1.2:
        fragile.append("ADX gate 25 breaks h2")
    neigh_pass = sum(1 for v in neigh.values() if v["pass_pf12"])
    verdict = {
        "base_pass_h1_h2": h1pf >= 1.2 and h2pf >= 1.2 and fee_pass,
        "quarters_pf_ge_1": q_pos,
        "quarters_detail": q_pfs,
        "neighbor_pass_count": f"{neigh_pass}/{len(neigh)}",
        "cpp_pf12_hits": len(report["sensitivity_cpp"]["hits_pf12"]),
        "fragile": fragile,
        "promote": None,
    }
    # promote only if base pass, >=3/4 quarters PF>=1, and at least 3/7 neighbors pass
    verdict["promote"] = bool(
        verdict["base_pass_h1_h2"] and q_pos >= 3 and neigh_pass >= 3 and not (
            "fails at 10bps/side fee" in fragile and fees.get("0.0012", {}).get("pass_pf12") is False
        )
    )
    # softer: research-keep vs LIVE
    if verdict["base_pass_h1_h2"] and q_pos >= 2 and neigh_pass >= 2:
        verdict["status"] = "RESEARCH_KEEP"
    else:
        verdict["status"] = "FRAGILE"
    if verdict["base_pass_h1_h2"] and q_pos >= 3 and neigh_pass >= 4 and fees.get("0.001", {}).get("pass_pf12"):
        verdict["status"] = "PROMOTE_CANDIDATE"
    report["verdict"] = verdict

    # restore base strat
    patch_strat(BASE["mode"], BASE["adx_min"], BASE["rsi_max"], BASE["sl"], BASE["tp"])
    ensure_ft_config()

    (OUT / "deep-summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("VERDICT", verdict, flush=True)
    print("wrote", OUT / "deep-summary.json", flush=True)


if __name__ == "__main__":
    main()
