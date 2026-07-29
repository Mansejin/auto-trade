from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

INTEGRITY_FIELD = "_integrity"


def canonical_json(data: dict[str, Any]) -> bytes:
    payload = {k: v for k, v in data.items() if k != INTEGRITY_FIELD}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_dict(data: dict[str, Any], key: str) -> str:
    return hmac.new(key.encode("utf-8"), canonical_json(data), hashlib.sha256).hexdigest()


def attach_integrity(data: dict[str, Any], key: str) -> dict[str, Any]:
    out = {k: v for k, v in data.items() if k != INTEGRITY_FIELD}
    if not key:
        return out
    out[INTEGRITY_FIELD] = sign_dict(out, key)
    return out


def verify_dict(data: dict[str, Any], key: str) -> bool:
    if not key:
        return True
    sig = data.get(INTEGRITY_FIELD)
    if not sig:
        return True
    body = {k: v for k, v in data.items() if k != INTEGRITY_FIELD}
    expected = sign_dict(body, key)
    return hmac.compare_digest(str(sig), expected)


def restrict_path_mode(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        logger.debug("could not chmod %s to 0600", path, exc_info=True)
