"""Assist manual channel sampling: print swing pivots + naive channel-event candidates.

Not a strategy. Output is for human review into channel-manual-sample-log.csv.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).with_name("data") / "qqq_usdt_4h.json"
SWING = 3  # bars left/right
VOL_SMA = 20


@dataclass
class Bar:
    ts: int
    o: float
    h: float
    l: float
    c: float
    v: float

    @property
    def dt(self) -> str:
        return datetime.fromtimestamp(self.ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def load() -> list[Bar]:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    return [
        Bar(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]))
        for r in raw
    ]


def pivots(bars: list[Bar]) -> tuple[list[int], list[int]]:
    hi, lo = [], []
    for i in range(SWING, len(bars) - SWING):
        window = bars[i - SWING : i + SWING + 1]
        if bars[i].h == max(b.h for b in window):
            hi.append(i)
        if bars[i].l == min(b.l for b in window):
            lo.append(i)
    return hi, lo


def vol_avg(bars: list[Bar], i: int) -> float:
    a = max(0, i - VOL_SMA + 1)
    chunk = bars[a : i + 1]
    return sum(b.v for b in chunk) / len(chunk)


def line_y(i0: int, y0: float, i1: int, y1: float, i: int) -> float:
    if i1 == i0:
        return y0
    return y0 + (y1 - y0) * (i - i0) / (i1 - i0)


def main() -> None:
    bars = load()
    hi_idx, lo_idx = pivots(bars)
    print(f"bars={len(bars)} swing_highs={len(hi_idx)} swing_lows={len(lo_idx)}")
    print("--- recent swing highs ---")
    for i in hi_idx[-25:]:
        va = vol_avg(bars, i)
        flag = "VOL*" if bars[i].v >= 1.5 * va else ""
        print(f"H {bars[i].dt} h={bars[i].h:.2f} v={bars[i].v:.0f} vs_sma={bars[i].v/va:.2f} {flag}")
    print("--- recent swing lows ---")
    for i in lo_idx[-25:]:
        va = vol_avg(bars, i)
        flag = "VOL*" if bars[i].v >= 1.5 * va else ""
        print(f"L {bars[i].dt} l={bars[i].l:.2f} v={bars[i].v:.0f} vs_sma={bars[i].v/va:.2f} {flag}")

    # Naive ascending-channel candidates: last 2 lows define base; nearest high sets width;
    # scan forward for touches / closes outside.
    print("\n=== ASC channel candidates (2 lows + parallel via high) ===")
    n_cand = 0
    for a in range(len(lo_idx) - 1):
        i0, i1 = lo_idx[a], lo_idx[a + 1]
        if i1 - i0 < 6 or i1 - i0 > 60:
            continue
        y0, y1 = bars[i0].l, bars[i1].l
        slope = (y1 - y0) / (i1 - i0)
        if slope <= 0:
            continue
        # opposing high between or shortly after
        highs_between = [j for j in hi_idx if i0 < j <= i1 + 8]
        if not highs_between:
            continue
        jh = max(highs_between, key=lambda j: bars[j].h - line_y(i0, y0, i1, y1, j))
        width = bars[jh].h - line_y(i0, y0, i1, y1, jh)
        if width <= 0 or width / bars[jh].h < 0.005:
            continue
        # third touch on lower or upper within next 40 bars after i1
        end = min(len(bars) - 1, i1 + 50)
        lower_touches = 0
        upper_touches = 0
        events = []
        for i in range(i1 + 1, end + 1):
            lower = line_y(i0, y0, i1, y1, i)
            upper = lower + width
            # bounce near lower
            if bars[i].l <= lower * 1.002 and bars[i].c > lower and bars[i].c > bars[i].o:
                lower_touches += 1
                va = vol_avg(bars, i)
                events.append(("A_bounce_lower", i, bars[i].v / va))
            # bounce near upper
            if bars[i].h >= upper * 0.998 and bars[i].c < upper and bars[i].c < bars[i].o:
                upper_touches += 1
                va = vol_avg(bars, i)
                events.append(("A_bounce_upper", i, bars[i].v / va))
            # close outside upper
            if bars[i].c > upper * 1.001:
                va = vol_avg(bars, i)
                events.append(("B_break_upper", i, bars[i].v / va))
                # look for retest next 12 bars
                for k in range(i + 1, min(len(bars), i + 13)):
                    u = line_y(i0, y0, i1, y1, k) + width
                    if bars[k].l <= u * 1.003 and bars[k].c >= u * 0.998:
                        events.append(("B_retest_upper", k, bars[k].v / vol_avg(bars, k)))
                        break
                    if bars[k].c < u * 0.997:
                        events.append(("B_retest_fail_upper", k, bars[k].v / vol_avg(bars, k)))
                        break
                break
            if bars[i].c < lower * 0.999:
                va = vol_avg(bars, i)
                events.append(("B_break_lower", i, bars[i].v / va))
                break
        if lower_touches + upper_touches < 1 and not any(e[0].startswith("B_") for e in events):
            continue
        n_cand += 1
        print(
            f"\n#{n_cand} L0={bars[i0].dt}@{y0:.2f} L1={bars[i1].dt}@{y1:.2f} "
            f"H={bars[jh].dt}@{bars[jh].h:.2f} width={width:.2f} ({100*width/bars[jh].h:.2f}%)"
        )
        for kind, i, vr in events[:8]:
            print(f"  {kind:22} {bars[i].dt} c={bars[i].c:.2f} volx={vr:.2f}")
        if n_cand >= 40:
            break

    print("\n=== DESC channel candidates (2 highs + parallel via low) ===")
    n_cand = 0
    for a in range(len(hi_idx) - 1):
        i0, i1 = hi_idx[a], hi_idx[a + 1]
        if i1 - i0 < 6 or i1 - i0 > 60:
            continue
        y0, y1 = bars[i0].h, bars[i1].h
        slope = (y1 - y0) / (i1 - i0)
        if slope >= 0:
            continue
        lows_between = [j for j in lo_idx if i0 < j <= i1 + 8]
        if not lows_between:
            continue
        jl = min(lows_between, key=lambda j: line_y(i0, y0, i1, y1, j) - bars[j].l)
        width = line_y(i0, y0, i1, y1, jl) - bars[jl].l
        if width <= 0 or width / bars[jl].l < 0.005:
            continue
        end = min(len(bars) - 1, i1 + 50)
        events = []
        for i in range(i1 + 1, end + 1):
            upper = line_y(i0, y0, i1, y1, i)
            lower = upper - width
            if bars[i].h >= upper * 0.998 and bars[i].c < upper and bars[i].c < bars[i].o:
                events.append(("A_bounce_upper", i, bars[i].v / vol_avg(bars, i)))
            if bars[i].l <= lower * 1.002 and bars[i].c > lower and bars[i].c > bars[i].o:
                events.append(("A_bounce_lower", i, bars[i].v / vol_avg(bars, i)))
            if bars[i].c < lower * 0.999:
                events.append(("B_break_lower", i, bars[i].v / vol_avg(bars, i)))
                for k in range(i + 1, min(len(bars), i + 13)):
                    lo = line_y(i0, y0, i1, y1, k) - width
                    if bars[k].h >= lo * 0.997 and bars[k].c <= lo * 1.002:
                        events.append(("B_retest_lower", k, bars[k].v / vol_avg(bars, k)))
                        break
                    if bars[k].c > lo * 1.003:
                        events.append(("B_retest_fail_lower", k, bars[k].v / vol_avg(bars, k)))
                        break
                break
            if bars[i].c > upper * 1.001:
                events.append(("B_break_upper", i, bars[i].v / vol_avg(bars, i)))
                break
        if not events:
            continue
        n_cand += 1
        print(
            f"\n#{n_cand} H0={bars[i0].dt}@{y0:.2f} H1={bars[i1].dt}@{y1:.2f} "
            f"L={bars[jl].dt}@{bars[jl].l:.2f} width={width:.2f} ({100*width/bars[jl].l:.2f}%)"
        )
        for kind, i, vr in events[:8]:
            print(f"  {kind:22} {bars[i].dt} c={bars[i].c:.2f} volx={vr:.2f}")
        if n_cand >= 40:
            break


if __name__ == "__main__":
    main()
