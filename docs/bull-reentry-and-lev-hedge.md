# Bull-cycle re-entry + Bitget leverage swing/hedge (design)

> Status: **design only** (2026-08-05). Not LIVE. Does not change Policy C CORE map.  
> Related: [`dual-sleeve-allocation.md`](dual-sleeve-allocation.md) · [`regime-auto-switch-playbook.md`](regime-auto-switch-playbook.md) · [`config/sleeves.json`](../config/sleeves.json)

## Why

1. CORE bear card (`m5-v6`) is **not** scored on roaring bulls — holdout underperformance is in-scope to ignore for that sleeve.
2. When a **major bull cycle** returns, waiting on `bull → bull-v2` alone may be late/choppy; need an explicit **re-entry timing** layer.
3. Some capital should stay on **Bitget leveraged swing** even in bulls — profit participation **and** a fast hedge/flat when the trend breaks (spot CORE stays long-biased).

## Guardrails (do not break)

| Rule | Note |
|------|------|
| CORE map frozen until audit | Still Policy C: bull/transition→`bull-v2`, bear→`m5-v6`, sideways→Williams(+dwell→v5) |
| Venue split | 장타 Upbit / 레버리지·헷지 Bitget — do not point Upbit bot at futures JSON |
| SCALP LIVE off until falsification | Bitget slot stays cash until a card passes multi-window + human approve |
| No long→short mirror hunt as default | Already falsified for bear scalp |

---

## Need A — Major-bull re-entry timing (CORE)

### Problem

Regime flip `bear/transition → bull` is a **classification** event, not a **good spot entry**. Jumping straight into `bull-v2` on first bull day can buy into dead-cat / fake reclaim.

### Proposed layer (above or beside map)

Keep Strategy Path switching as today. Add a **re-entry gate** that only delays **new** CORE buys after a bull (or transition→bull) promotion:

| Gate | Idea (falsify separately) | Default sketch |
|------|---------------------------|----------------|
| G1 Regime confirm | Need N closed daily bars in `bull` (or dwell on transition→bull) | N=2~3 d |
| G2 Structure | Price reclaim SMA50 **and** hold 1d close above it | 1 confirm close |
| G3 Trend fuel | ADX rising **or** +DI > −DI for M bars | M=2 |
| G4 Timing TF | Enter on bull sleeve TF (`4h`) pullback rule, not market-on-open | reuse/extend `bull-v2` pullback — do not invent a third strategy until G1–G3 fail |

**Behaviour when gated:** CORE may switch file to `bull-v2` for consistency with map, but **entries blocked** (`hold` force) until gates pass — or delay file switch until gates pass (prefer **delay file switch** so desk/status stay honest).

**Falsify (before LIVE):**

- Window set: last 2 major reclaim episodes + 1 fake reclaim (define dates in research note when implementing).
- Kill if: gate adds &gt;X% missed move vs ungated `bull-v2` **and** does not cut fake-reclaim MDD.
- Kill if: trades after gate &lt; 5 on combined reclaim windows (sample fail → inconclusive, widen windows).

**Non-goals:** predicting cycle tops; changing bear→m5-v6 mapping.

---

## Need B — Bull-market Bitget leveraged swing (+ hedge)

### Role split

| Book | Venue | Job in bull |
|------|-------|-------------|
| CORE | Upbit spot | Cycle beta / Policy C long swing |
| LEV (new name — not old 10m “scalp”) | Bitget UTA | Smaller notionals, leverage swing; **flatten/short/hedge** when trend breaks |

Rename in docs/config when implemented: prefer `lev_swing` over recycling `scalp` so fee/TF assumptions stay distinct from falsified Div ATR daytrade.

### Map sketch (Bitget only)

| Regime | LEV slot | Intent |
|--------|----------|--------|
| bull / transition | long-biased leverage swing (survivor TBD) | participate with defined SL |
| trend-break overlay | reduce / flat / short hedge | triggered by structure break, not by regime label alone |
| bear | cash **or** short swing (only after new falsification) | do not revive Div ATR by default |
| sideways | cash or mean-revert lev (TBD) | optional later |

### Trend-break overlay (hedge use)

Independent of daily regime string — can fire **inside** a bull sleeve:

1. **Break:** 4h/1d close back below SMA50 (or bull swing swing-low), **and** +DI/−DI flip or ADX drop rule (pick one family, falsify).
2. **Action (pick one, do not stack):**  
   - A: Bitget flat only (de-risk lev book)  
   - B: small hedge short vs CORE notional band (e.g. target hedge_pct of CORE BTC exposure)  
   - C: flip LEV to short swing card
3. **Core untouched** unless human policy later allows spot sell — default **CORE holds Policy C exits only**.

### Capital / risk (intent)

- LEV gross ≤ frozen sleeve pct (today intent 50% Bitget — until funded, still cash).
- Max leverage hard-cap in bot env (existing Bitget runner bounds).
- Hedge notionals capped so CORE + LEV net beta cannot silently go −200% on a spike.

### Falsify before LIVE

- Multi-window: bull participation + at least one break/hedge episode.
- Fee stress (≥1× Bitget fee) and funding drag.
- Compare to cash Bitget during same windows (cash must not dominate on MDD+return jointly without clear upside).

---

## Implementation order (when leaving design)

1. Spec dates for last cycle reclaim / fake reclaim → test Need A gates as a thin `entry_gate` (or delayed switch) on top of existing switcher.  
2. Promote **one** Bitget `lev_swing` JSON through create-strategy → backtest falsify → only then `scalp-live-map` / rename.  
3. Add trend-break overlay as second PR (hedge action A first — flat-only is smallest).  
4. Desk: show gate state + LEV slot next to CORE meters.

## Explicitly deferred

- Auto TRX bridge / rebalance under 500k KRW.  
- Changing Policy C file map.  
- Using m5-v6 on Bitget short invert as bull hedge (separate study only).
