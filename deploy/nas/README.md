# NAS deploy (Synology / saenggibu)

OCI VPS 대신 회사 NAS Docker에서 실행.

## Layout

- Host path: `/volume1/docker/p3f8c1a2` (opaque; mapping only in local `name-map.local.md`)
- Compose: `docker-compose.nas.yml` (edge/LE 없음), project `p3f8c1a2`
- Containers: `p3f8c1a2-w1`…`w4` (CF Tunnel still resolves alias `desk` → w3)
- Public: Cloudflare Tunnel → `http://desk:8080`
- Worker `mansejin.com/autotrade` ORIGIN → tunnel hostname

## One-time Cloudflare

1. Zero Trust → Networks → Tunnels → Create (`autotrade-nas`)
2. Public hostname: `autotrade-origin.mansejin.com` → `http://desk:8080`
3. Copy token → `.env` `CLOUDFLARE_TUNNEL_TOKEN=...`
4. DNS: `autotrade-origin` CNAME → `xxxx.cfargotunnel.com` (Proxied)

## Fast UI deploy (Windows → NAS)

Static/code are bind-mounted into desk (`w3`). **Do not `--build` for CSS/JS tweaks.**

```powershell
# ~1-2s — static only
pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/static/desk.js,web/static/desk.css

# ~5s — after app.py change
pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/app.py -RestartDesk

# ~40s+ — Dockerfile / pip only
pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/Dockerfile -RebuildDesk
```

## Start

```bash
cd /volume1/docker/p3f8c1a2
sudo docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile tunnel up -d --build
sudo docker compose -p p3f8c1a2 -f docker-compose.nas.yml ps
curl -sS http://127.0.0.1:18080/autotrade/healthz
```

Name remapping helper (NAS): `deploy/nas/obfuscate-nas.sh`  
Local-only map: `deploy/nas/name-map.local.md` (gitignored).

SSH alias: `saenggibu-nas-local` (link-local). Tailscale host may refuse SSH.

## API IP allowlist (required)

NAS egress IP must be allowed on exchange API keys (VPS IP alone will fail after move).

```bash
curl -sS https://api.ipify.org && echo
# current company NAS: 115.142.61.173
```

- Upbit Open API → IP 허용 목록에 NAS 공인 IP 추가  
- Bitget API Key → IP whitelist에 동일 IP 추가  
- 반영 후: `sudo docker compose -f docker-compose.nas.yml restart bot bot-bitget`

## Synology notes

- Use `sudo docker` (`/usr/local/bin/docker`).
- Prefer `user: "0:0"` on bots; avoid `read_only` on shared folders.
- If `data/` / `logs/` files are owned by uid 10001 and unwritable, wipe via a root container then recreate.
- `.env` must be real LF newlines (not literal `\n`). Helper: `deploy/nas/merge_env.py`.
