# AGENTS.md

## Cursor Cloud specific instructions

This repo is an Upbit auto-trading project with two runnable Python services plus a set of
`uv`-based agent skills. Standard commands and env vars are documented in `README.md`; the notes
below cover only the non-obvious caveats for running things locally (outside Docker) in this env.

### Services

- **bot** — PAPER/LIVE trading loop. Entry: `python -m bot`. Deps: `requirements.txt` (httpx, PyJWT).
- **desk** — FastAPI dashboard (`web/app.py`), served by uvicorn. Deps: `web/requirements.txt`.
- `docker-compose.yml` is the production/deploy path (bot + desk + nginx edge). For local dev,
  run the two Python processes directly instead of Docker.

### Environment / setup

- The startup update script creates a repo-root `.venv` and installs both `requirements.txt` and
  `web/requirements.txt`. Use `./.venv/bin/python` / `./.venv/bin/uvicorn`. (`.venv/`, `data/`,
  `logs/`, `.env` are gitignored.)
- No formal test or lint framework is configured. Basic syntax check:
  `./.venv/bin/python -m compileall bot web/app.py`.
- The backtest / create-strategy skills under `.agents/skills/` use `uv`/`uvx` (see
  `.agents/skills/setup/SKILL.md`), which is independent of the bot `.venv`.

### Running the bot (non-obvious)

- `bot/config.py` reads config from the **process environment only** — there is NO dotenv loading.
  `.env` is consumed by docker compose, not by `python -m bot`. For local runs you must export vars
  inline, e.g. `BOT_ROOT=/workspace PAPER=true POLL_SECONDS=5 ./.venv/bin/python -m bot`.
- Paths are resolved relative to `BOT_ROOT` (defaults to `/app`, the Docker layout). Locally set
  `BOT_ROOT=/workspace` (or set `STRATEGY_PATH`/`STATE_PATH`/`LOG_DIR` explicitly) or it will look
  under `/app` and fail to find strategies.
- Default `PAPER=true` is safe: virtual fills only, no API keys needed. LIVE requires
  `UPBIT_ACCESS_KEY` + `UPBIT_SECRET_KEY` + `LIVE_CONFIRM=I_UNDERSTAND_LIVE_TRADING_RISK`; do not
  enable it during setup/testing.
- The bot fetches live candles from `api.upbit.com` every tick (even in PAPER), so it needs
  outbound network access.

### Running the desk dashboard (non-obvious)

- Fail-closed: if `DASHBOARD_TOKEN` is empty the status API stays unauthorized; if set it must be
  >= 32 chars. Log in by POSTing the token + CSRF hidden field to `/login` (or use the login page);
  auth is stored as an httpOnly cookie. `?token=` in the URL is intentionally not accepted.
- Rate limiting uses `X-Real-IP` (set by nginx/Cloudflare Worker), not client `X-Forwarded-For`.
- Run uvicorn from the `web/` directory (`uvicorn app:app`), since the static dir is resolved
  relative to `app.py`. Use `--forwarded-allow-ips=` so uvicorn does not trust client
  `X-Forwarded-For` for `request.client.host` (rate limiting uses `X-Real-IP` or the peer).
- The desk does not talk to the bot over the network — it reads the bot's shared files
  (`logs/status.json`, `logs/latest_status.txt`, `data/state.json`, `data/risk.json`). Point the
  desk's `LOG_DIR`/`STATE_PATH`/`RISK_PATH` at the same dirs the bot writes to so it shows live status.

### Treasury (Upbit <-> Bitget)

- Bridge coin: **TRX** (cheap withdraw). Paths: KRW->TRX->Bitget->USDT, and reverse USDT->TRX->Upbit->KRW.
- Hybrid 50:50: REBALANCE_ENABLED=true, band default **12%p**, alert cooldown + transfer cooldown.
  Bot proposes on band breach; execute only via /리밸런스승인. Manual /리밸런스, /원화준비 <원>, /자산.
- Use cases: fund Bitget only on futures need; park spending cash on Upbit; avoid fee-churn with band+cooldown.

### Bitget UTA + Agent MCP

- Trading client is **UTA API v3** (`bot/bitget_client.py`): candles `/api/v3/market/candles`,
  orders `/api/v3/trade/place-order`, assets `/api/v3/account/assets`, withdraw
  `/api/v3/account/withdraw`. Docs: https://www.bitget.com/api-doc/uta/intro
- Parallel container: `bot-bitget` (`EXCHANGE=bitget`). Category via `BITGET_CATEGORY`.
  Strategy may set `funding.enabled` to auto bridge Upbit KRW→TRX→Bitget TRX→USDT when a
  futures buy signal arrives with insufficient margin — requires `TRANSFER_*` env + withdraw
  permission. No Telegram approve on that path; manual `/이체요청` still exists on Upbit bot.
- Demo Trading: set `BITGET_PAPER_TRADING=true` **and** Demo API keys (sends `paptrading: 1`).
- Cursor MCP: copy `.cursor/mcp.json.example` → `.cursor/mcp.json` (gitignored) and fill
  `BITGET_*`. Runs `npx -y @bitget-ai/bitget-agent-mcp --read-only`. Never commit real keys.
  Official package: https://www.npmjs.com/package/@bitget-ai/bitget-agent-mcp — Agent Hub:
  https://github.com/Bitget-AI/agent_hub
- Older npm name `bitget-mcp-server` is superseded; prefer `@bitget-ai/bitget-agent-mcp`.
