"""나씨 3틱 카운트 상태머신 (정리본 규칙).

- 의미 있는 음봉만 틱으로 셈 (body ≥ body_k × median)
- 직전 틱 대비 현저히 짧은 음봉은 세지 않음
- 짧은 봉(비의미)이 sideways_reset개 연속이면 카운트 리셋
- 의미 있는 양봉이면 카운트 리셋
- 첫 틱: 직전 양봉보다 짧으면, 종가가 직전 양봉 시가 아래로 깨야 1틱
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def three_tick_entries(
    open_: pd.Series,
    close: pd.Series,
    *,
    body_k: float = 1.5,
    lookback: int = 20,
    short_frac: float = 0.5,
    sideways_reset: int = 3,
) -> tuple[pd.Series, pd.Series]:
    o = open_.to_numpy(dtype=float)
    c = close.to_numpy(dtype=float)
    body = np.abs(c - o)
    med = pd.Series(body).rolling(lookback).median().to_numpy()
    n = len(c)
    enter = np.zeros(n, dtype=bool)
    counts = np.zeros(n, dtype=np.int16)

    count = 0
    prev_tick_body: float | None = None
    sideways_run = 0

    for i in range(n):
        m = med[i]
        if not np.isfinite(m) or m <= 0:
            counts[i] = count
            continue

        b = body[i]
        meaningful = b >= body_k * m
        is_red = c[i] < o[i]
        is_green = c[i] > o[i]

        if not meaningful:
            sideways_run += 1
            if sideways_run >= sideways_reset:
                count = 0
                prev_tick_body = None
            counts[i] = count
            continue

        sideways_run = 0

        if is_green:
            count = 0
            prev_tick_body = None
            counts[i] = 0
            continue

        if not is_red:
            counts[i] = count
            continue

        # meaningful red
        if prev_tick_body is not None and b < short_frac * prev_tick_body:
            counts[i] = count
            continue

        if count == 0:
            if i > 0 and c[i - 1] > o[i - 1]:
                prev_green_body = body[i - 1]
                if b < prev_green_body and c[i] >= o[i - 1]:
                    # 반전만 인지, 아직 1틱 아님
                    counts[i] = 0
                    continue
            count = 1
            prev_tick_body = b
        else:
            count += 1
            prev_tick_body = b

        counts[i] = count
        if count >= 3:
            enter[i] = True
            count = 0
            prev_tick_body = None

    return (
        pd.Series(enter, index=open_.index),
        pd.Series(counts, index=open_.index),
    )
