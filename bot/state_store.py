from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from bot.integrity import restrict_path_mode

logger = logging.getLogger(__name__)


def load_state(path: Path, default_cash: float) -> Portfolio:
    if not path.exists():
        logger.info("state missing; starting paper cash=%.0f", default_cash)
        return Portfolio(cash=default_cash)
    data = json.loads(path.read_text(encoding="utf-8"))
    return Portfolio.from_dict(data, default_cash=default_cash)


def save_state(path: Path, portfolio: Portfolio, extra: dict[str, Any] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = portfolio.to_dict()
    if extra:
        payload.update(extra)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    restrict_path_mode(path)
