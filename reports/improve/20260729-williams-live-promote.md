# LIVE promote — Williams sideways (human approve 2026-07-29)

## Change
Policy C `sideways` → `regime-sideways-mr-1h-williams-v1.json`
Gate: sideways dwell < 7 → fallback `regime-sideways-mr-4h-v5.json`

## Files
- `scripts/remote_regime_switch.py`
- `scripts/premium_watcher.py` (restore uses regime-current selected_file)
- strategy already in repo

## Not changed
- bull / bear / transition map
- frozen Williams thresholds
- kimchi premium overlay logic

## Risk note
Research showed dwell7 helps vs stubs but strategy still trails buy&hold in many sideways windows.
User explicitly requested LIVE with small capital; paper skipped.
