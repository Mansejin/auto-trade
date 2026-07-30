# Exchange MCP setup (Bitget + Upbit)

Local Cursor agents and (when Cloud MCP is wired) automations can read market/account state without pasting keys into prompts.

`.cursor/` is gitignored. Copy the example into the local MCP file:

```bash
# from repo root
mkdir -p .cursor
cp docs/mcp.example.json .cursor/mcp.json
# merge with any existing servers (Cloudflare etc.) if needed
```

Keys stay in gitignored `.env` via `dotenv-cli`. Never put API secrets in `mcp.json`, commits, or automation prompts.

## Required `.env` keys

| Var | Purpose |
|-----|---------|
| `BITGET_API_KEY` | Bitget UTA |
| `BITGET_SECRET_KEY` | Bitget UTA |
| `BITGET_PASSPHRASE` | Bitget UTA |
| `UPBIT_ACCESS_KEY` | Upbit Open API |
| `UPBIT_SECRET_KEY` | Upbit Open API |

## Safety posture

| Server | Package | Write trades |
|--------|---------|--------------|
| **bitget** | `@bitget-ai/bitget-agent-mcp --read-only` | Blocked by flag |
| **upbit** | `@iqai/mcp-upbit` | Package gates private tools behind `UPBIT_ENABLE_TRADING=true` (needed for balance/order **reads**). **Create the Upbit API key with 자산조회 + 주문조회 only** — no 주문하기 / 출금하기. Agents must not call `CREATE_*` / `CANCEL_*` / withdraw tools. |

If Bitget keys ever lived plaintext in `.cursor/mcp.json`, rotate them on Bitget.

## Cloud Automation secrets

Cloud runs do **not** get gitignored `.cursor/mcp.json` or local `.env`. For the 10m daytrade automation:

1. Cursor Automations / Cloud secrets: set the five env vars above (plus existing `AUTO_TRADE_BOT_SSH_KEY`).
2. Enable project MCP servers **bitget** and **upbit** for that automation if the UI exposes MCP toggles.
3. Prompt rules: MCP = health/spot-check only. Backtest remains `upbit-strategy-toolkit`. Deploy remains `scripts/deploy-strategy-to-bot.sh`. No MCP live orders.

## Agent usage (what helps the loop)

- **Upbit**: `GET_TICKER` / `GET_ORDERBOOK` for KRW-BTC spot check after deploy; `GET_ACCOUNTS` / `GET_ORDERS` for bot health — not for strategy edge.
- **Bitget**: `market` / `account_overview` / `position` for futures sleeve health — daytrade family stays Upbit toolkit JSON.
- Never use MCP to replace a failed backtest window or to “confirm” promotion bar A–D.
