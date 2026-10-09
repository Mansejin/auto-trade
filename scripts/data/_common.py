"""Shared helpers for scripts/data/fetch_*.py: polite GET, resumable CSV append."""
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "research"
OUT.mkdir(parents=True, exist_ok=True)

_client = httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": "auto-trade-research/1.0"})


def get(url, params=None, sleep=0.15, tries=6):
    """GET with retry/backoff on 429/418/5xx. Returns parsed JSON or text."""
    for i in range(tries):
        try:
            r = _client.get(url, params=params)
        except httpx.HTTPError as e:
            wait = 2 ** i
            print(f"  net error {e!r}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        if r.status_code in (418, 429) or r.status_code >= 500:
            wait = int(r.headers.get("Retry-After", 0)) or 2 ** (i + 1)
            print(f"  HTTP {r.status_code}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        time.sleep(sleep)
        if r.status_code in (400, 404):
            return None
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        return r.json() if "json" in ct else r.text
    raise RuntimeError(f"giving up: {url} {params}")


def ms_to_iso(ms):
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_to_ms(s):
    return int(datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)


def read_rows(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def last_by_key(path, key_cols, ts_col):
    """{key tuple: max int(ts)} from an existing CSV, for resuming."""
    out = {}
    for r in read_rows(path):
        k = tuple(r[c] for c in key_cols)
        t = int(r[ts_col])
        if t > out.get(k, -1):
            out[k] = t
    return out


def append_rows(path, header, rows):
    new = not path.exists()
    with open(path, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerows(rows)


def now_ms():
    return int(time.time() * 1000)


DAY_MS = 86_400_000
