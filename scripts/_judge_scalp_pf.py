"""Judge meaningful scalp PF bars, then re-grid at that bar."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "cpp-bt" / "build" / "cpp-bt.exe"
FEE = 0.0006
FEE_RT = FEE * 2


def approx_lo(n: int, pf: float) -> float | None:
    if n <= 1 or pf <= 0:
        return None
    # order-of-magnitude: log-PF ~ se 1.2/sqrt(n)
    se = 1.2 / math.sqrt(n)
    return pf * math.exp(-1.64 * se)


def load_top(name: str) -> dict:
    return json.loads((ROOT / "reports" / f"{name}-summary.json").read_text(encoding="utf-8"))


def best_in_top(s: dict, nmin: int) -> dict | None:
    rows = [
        r
        for r in s.get("top20", [])
        if r["windows"]["h1"]["trades"] >= nmin and r["windows"]["h2"]["trades"] >= nmin
    ]
    return rows[0] if rows else None


def judge() -> dict:
    print(f"round_trip_fee_bps={FEE_RT * 10000:.1f}")
    print("fee as fraction of typical scalp move M:")
    for m in (0.003, 0.005, 0.008, 0.010, 0.015, 0.030):
        print(f"  M={m * 100:.1f}% -> fee/M={FEE_RT / m:.1%}")

    verdict = {
        "fee_rt": FEE_RT,
        # After-fee PF>=1.0 is break-even. For scalp, demand buffer + sample size:
        # - n>=150/half: PF>=1.10 (weaker bar, larger sample)
        # - n>=100/half: PF>=1.15 (stronger bar)
        # Prefer the n>=150 / PF>=1.10 bar for "is 1.1 meaningful?" — yes IF n large,
        # BUT only after fees. fee0-only 1.1 is not bankable.
        "criteria_primary": {"min_pf": 1.10, "min_trades": 150, "fee": FEE},
        "criteria_strict": {"min_pf": 1.15, "min_trades": 100, "fee": FEE},
        "rationale": (
            "12bps RT eats 15-40% of a 0.3-0.8% scalp move, so after-fee PF must "
            "clear 1.0 with room. PF 1.1 is meaningful only with fat n (noise); "
            "n~100 needs ~1.15. fee=0 PF~1.13 with n>=100 is NOT enough - fees wipe it."
        ),
    }

    print("\n=== existing grids snapshot ===")
    for name, nmin in [
        ("trend_short_scalp_fade", 100),
        ("trend_short_scalp_fade_fee0", 100),
        ("trend_short_scalp_fade_fee0", 150),
        ("trend_short_scalp_1m", 200),
        ("trend_short_scalp_1m_fee0", 100),
        ("trend_short_scalp_1m_fee0", 200),
    ]:
        path = ROOT / "reports" / f"{name}-summary.json"
        if not path.exists():
            print(f"  {name} n>={nmin}: missing")
            continue
        s = load_top(name)
        r = best_in_top(s, nmin)
        if not r:
            print(f"  {name} n>={nmin}: no row in top20")
            continue
        h1, h2 = r["windows"]["h1"], r["windows"]["h2"]
        mn = min(h1["profit_factor"], h2["profit_factor"])
        lo = approx_lo(min(h1["trades"], h2["trades"]), mn)
        print(
            f"  {name} n>={nmin}: minPF={mn:.3f} "
            f"trades={h1['trades']}/{h2['trades']} approx_lo={None if lo is None else round(lo, 3)} "
            f"tag={r['tag']}"
        )

    print("\nVERDICT:")
    print(verdict["rationale"])
    print(
        "Re-search after-fee with primary "
        f"PF>={verdict['criteria_primary']['min_pf']} n>={verdict['criteria_primary']['min_trades']}"
    )
    return verdict


def write_grid(path: Path, base: str, timeframe_note: str, criteria: dict) -> None:
    # reuse fade grid structure; only criteria + base fee path
    src = ROOT / "cpp-bt" / "grids" / (
        "trend_short_scalp_1m.json" if "1m" in timeframe_note else "trend_short_scalp_fade.json"
    )
    g = json.loads(src.read_text(encoding="utf-8-sig"))
    g["base_strategy"] = base
    g["criteria"] = {
        "min_pf": criteria["min_pf"],
        "min_trades": criteria["min_trades"],
    }
    path.write_text(json.dumps(g, indent=2) + "\n", encoding="utf-8")


def run_grid(grid: Path) -> dict:
    subprocess.run([str(CPP), "grid", "--grid", str(grid), "--data", str(ROOT / "cpp-bt" / "data")], check=True)
    stem = grid.stem
    return json.loads((ROOT / "reports" / f"{stem}-summary.json").read_text(encoding="utf-8"))


def main() -> None:
    verdict = judge()
    out = ROOT / "reports" / "scalp-pf-threshold-20260805"
    out.mkdir(parents=True, exist_ok=True)
    (out / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")

    # Ensure fee=0.0006 bases (not fee0)
    base5 = ROOT / "cpp-bt" / "strategies" / "trend_short_scalp_base.json"
    base1 = ROOT / "cpp-bt" / "strategies" / "trend_short_scalp_1m_base.json"
    for p in (base5, base1):
        j = json.loads(p.read_text(encoding="utf-8-sig"))
        j["fee"] = FEE
        p.write_text(json.dumps(j, indent=2) + "\n", encoding="utf-8")

    crit = verdict["criteria_primary"]
    g5 = ROOT / "cpp-bt" / "grids" / "trend_short_scalp_fade_pf11.json"
    g1 = ROOT / "cpp-bt" / "grids" / "trend_short_scalp_1m_pf11.json"
    write_grid(g5, "strategies/trend_short_scalp_base.json", "5m", crit)
    write_grid(g1, "strategies/trend_short_scalp_1m_base.json", "1m", crit)

    print("\n=== re-search after-fee PF>=1.10 n>=150 ===")
    s5 = run_grid(g5)
    s1 = run_grid(g1)
    summary = {
        "verdict": verdict,
        "5m": {"hits": len(s5["hits"]), "combos": s5["combos"], "best": s5["top20"][0] if s5["top20"] else None},
        "1m": {"hits": len(s1["hits"]), "combos": s1["combos"], "best": s1["top20"][0] if s1["top20"] else None},
    }
    (out / "research-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"5m hits={len(s5['hits'])} best_minPF≈", end="")
    if s5["top20"]:
        b = s5["top20"][0]
        print(
            round(min(b["windows"]["h1"]["profit_factor"], b["windows"]["h2"]["profit_factor"]), 3),
            b["tag"],
            f"{b['windows']['h1']['trades']}/{b['windows']['h2']['trades']}",
        )
    else:
        print("none")
    print(f"1m hits={len(s1['hits'])} best_minPF≈", end="")
    if s1["top20"]:
        b = s1["top20"][0]
        print(
            round(min(b["windows"]["h1"]["profit_factor"], b["windows"]["h2"]["profit_factor"]), 3),
            b["tag"],
            f"{b['windows']['h1']['trades']}/{b['windows']['h2']['trades']}",
        )
    else:
        print("none")

    # also strict bar for completeness (criteria change only)
    crit2 = verdict["criteria_strict"]
    g5s = ROOT / "cpp-bt" / "grids" / "trend_short_scalp_fade_pf115.json"
    write_grid(g5s, "strategies/trend_short_scalp_base.json", "5m", crit2)
    s5s = run_grid(g5s)
    summary["5m_strict_pf115_n100"] = {
        "hits": len(s5s["hits"]),
        "best": s5s["top20"][0] if s5s["top20"] else None,
    }
    (out / "research-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"5m strict PF>=1.15 n>=100 hits={len(s5s['hits'])}")


if __name__ == "__main__":
    main()
