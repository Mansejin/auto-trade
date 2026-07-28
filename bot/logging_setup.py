from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logging(level: str, log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level, logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    bot_file = TimedRotatingFileHandler(
        log_dir / "bot.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        utc=False,
    )
    bot_file.setFormatter(fmt)
    bot_file.suffix = "%Y-%m-%d"
    root.addHandler(bot_file)

    # Quiet noisy HTTP library; we log friendly summaries ourselves.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def trade_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("bot.trades")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    log.propagate = True  # also go to bot.log / console
    handler = TimedRotatingFileHandler(
        log_dir / "trades.log",
        when="midnight",
        interval=1,
        backupCount=90,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    handler.suffix = "%Y-%m-%d"
    log.addHandler(handler)
    return log


def write_latest_status(log_dir: Path, text: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "latest_status.txt"
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_status_json(log_dir: Path, payload: dict) -> None:
    """Atomic JSON snapshot for the dashboard (no secrets)."""
    import json
    from datetime import datetime

    log_dir.mkdir(parents=True, exist_ok=True)
    data = dict(payload)
    data.setdefault("updated_at", datetime.now().isoformat(timespec="seconds"))
    path = log_dir / "status.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
