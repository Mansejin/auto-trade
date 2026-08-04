FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOT_ROOT=/app \
    PAPER=true \
    STRATEGY_PATH=/app/strategies/sma_cross_btc.json \
    STATE_PATH=/app/data/state.json \
    POLL_SECONDS=300 \
    PAPER_CASH=1000000 \
    LOG_LEVEL=INFO

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot
COPY strategies ./strategies

RUN mkdir -p /app/data /app/logs \
    && useradd --create-home --uid 10001 bot \
    && chown -R bot:bot /app

USER bot

CMD ["python", "-m", "bot"]
