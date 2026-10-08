# NAS opaque names — agent reference

**Audience:** Cursor / coding agents operating on this repo or the company Synology NAS.  
**Language:** English (canonical; do not invent Korean folder names).  
**Purpose:** Host folders and Docker names were intentionally obfuscated so casual File Station browsing does not advertise trading or project brands. Use the codes below; never recreate the old human-readable paths.

---

## Critical rules (read first)

1. **There is no** `/volume1/docker/auto-trade` on the NAS. The live stack lives at **`/volume1/docker/p3f8c1a2`**.
2. Compose **project name** and **directory basename** are both `p3f8c1a2`. Always pass `-p p3f8c1a2`.
3. Service keys in compose are `w1`…`w5`, **not** `bot` / `bot-bitget` / `desk` / `cloudflared`.
4. Cloudflare Tunnel still targets Docker DNS alias **`desk`** → service **`w3`**. Do **not** remove `networks.net.aliases: [desk]` from `w3`.
5. Do **not** place `AGENTS.md`, `README.md`, or `ARCHITECTURE.md` at the **root** of `/volume1/docker/p3f8c1a2` — `deploy/nas/obfuscate-nas.sh` deletes those on purpose. Keep agent docs under `deploy/nas/` or in git (`docs/agents/`).
6. Secrets stay in `.env` (gitignored). Never commit API keys, tunnel tokens, or `DASHBOARD_TOKEN`.

---

## This repo (auto-trade) — canonical map

| Opaque id | Role | Notes |
|-----------|------|--------|
| `/volume1/docker/p3f8c1a2` | Deploy root for this repo | Bind-mounts `bot/`, `web/`, `data/`, `logs/`, `strategies/`, etc. |
| Compose project `p3f8c1a2` | `docker compose -p …` | Matches `name:` in `docker-compose.nas.yml` |
| Network `p3f8c1a2-net` | Bridge | Internal only |
| `p3f8c1a2-w1` / service `w1` | Upbit spot bot | Image `p3f8c1a2-w1:latest` |
| `p3f8c1a2-w2` / service `w2` | Bitget bot (main / non-scalp) | Image `p3f8c1a2-w2:latest` |
| `p3f8c1a2-w3` / service `w3` | Desk (FastAPI dashboard) | Alias **`desk`**; LAN debug `127.0.0.1:18080→8080` |
| `p3f8c1a2-w4` / service `w4` | cloudflared | Compose profile **`tunnel`** |
| `p3f8c1a2-w5` / service `w5` | Freqtrade Bitget scalp | Compose profile **`scalp`** |

### Compose cheat sheet

```bash
cd /volume1/docker/p3f8c1a2

# Core bots + desk
sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml up -d

# + Cloudflare tunnel
sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile tunnel up -d

# + scalp FT bot
sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile scalp up -d w5

sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml ps
curl -sS http://127.0.0.1:18080/autotrade/healthz
```

Public desk: Worker `https://mansejin.com/autotrade` → tunnel hostname → `http://desk:8080`.

SSH host alias (from operator machine): `saenggibu-nas-local` (link-local). Prefer `sudo -n docker` / `/usr/local/bin/docker` on the NAS.

### Related host paths (not under docker/)

| Path | Purpose |
|------|---------|
| `/usr/local/bin/ohola-tasks/*.sh` | DSM Task Scheduler wrappers (backup, other stacks) |
| `/volume1/99. 백업/ohola-docker/` | Local docker backup tarballs |

---

## Other stacks on the same NAS (company-wide)

Agents that list `/volume1/docker` will only see opaque `p*` directories. Decode with this table:

| Host directory | Human purpose | Containers / services |
|----------------|---------------|------------------------|
| `/volume1/docker/p3f8c1a2` | **auto-trade** (this repo) | `w1` Upbit, `w2` Bitget, `w3` desk, `w4` tunnel, `w5` scalp FT |
| `/volume1/docker/p91b4e07` | receipt-bot | `p91b4e07-w1` |
| `/volume1/docker/p2c6d9e1` | saenggibu | `w1` api (`sgb-api` DNS), `w2` gateway (`sgb-gateway`), `w3` tunnel |
| `/volume1/docker/p5a0f33c` | siyan-upload-api | `p5a0f33c-w1` |
| `/volume1/docker/p8e1b72d` | works-site | `w1` works-api, `w2` conti-collab |
| `/volume1/docker/p6d4a190` | tools-site (ticket-queue) | `w1` api, `w2` redis, `w3` tunnel |
| `/volume1/docker/p0c9e4f5` | openclaw | `p0c9e4f5-w1` |

Internal Docker DNS names such as `sgb-api` / `sgb-gateway` may remain readable for app wiring even though **folder** names are opaque. Prefer those DNS names inside compose networks; do not rename folders back to brand names.

---

## Anti-patterns (common agent mistakes)

| Mistake | Correct action |
|---------|----------------|
| `cd /volume1/docker/auto-trade` | `cd /volume1/docker/p3f8c1a2` |
| `docker compose … restart bot` | `… restart w1` (or `w2` / `w3`) |
| Looking for container `auto-trade-desk` | Use `p3f8c1a2-w3` or alias `desk` |
| Recreating a folder named `auto-trade` “for clarity” | Never — breaks ops and defeats obfuscation |
| Committing `deploy/nas/name-map.local.md` | Prefer this git doc; keep local map gitignored if duplicated |
| Leaving brand README at deploy **root** on NAS | Keep docs under `deploy/nas/` or only in git |

---

## Where this file lives

| Location | Why |
|----------|-----|
| **Git (canonical):** `docs/agents/nas-opaque-names.md` | Always available to agents cloning the private repo |
| **NAS mirror:** `/volume1/docker/p3f8c1a2/deploy/nas/opaque-names.agent.md` | Same content for SSH sessions without a fresh clone |
| Optional local: `deploy/nas/name-map.local.md` | Gitignored duplicate; do not rely on it in CI |

Helper that performed the rename: `deploy/nas/obfuscate-nas.sh`.  
Human ops notes (Korean/mixed): `deploy/nas/README.md`, `deploy/nas/BACKUP.md`.

---

## Quick identity check

If `ls /volume1/docker` shows `p3f8c1a2` and `docker ps` shows `p3f8c1a2-w1`…`w4`, you are on the obfuscated layout. Treat any leftover `auto-trade` path as **stale** and migrate or delete — do not run a second stack there.
