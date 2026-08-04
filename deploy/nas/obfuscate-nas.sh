#!/bin/sh
# Run ON NAS as ohola (needs passwordless sudo docker).
# Renames host folders + container_name / image labels to opaque codes.
set -eu
PATH=/usr/local/bin:/usr/bin:$PATH
DOCKER="sudo -n docker"

rename_dir() {
  old="$1"
  new="$2"
  if [ -d "$old" ] && [ ! -d "$new" ]; then
    mv "$old" "$new"
    echo "mv $old -> $new"
  elif [ -d "$new" ]; then
    echo "ok exists $new"
  else
    echo "skip missing $old"
  fi
}

echo "== stop stacks =="
$DOCKER compose -f /volume1/docker/auto-trade/docker-compose.nas.yml --profile tunnel down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/p3f8c1a2/docker-compose.nas.yml --profile tunnel down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/receipt-bot/docker-compose.yml down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/saenggibu/docker-compose.yml -f /volume1/docker/saenggibu/docker-compose.cloudflare.yml down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/siyan-upload-api/docker-compose.yml down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/works-site/api/docker-compose.yml down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/tools-site/ticket-queue-api/docker-compose.yml down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/tools-site/ticket-queue-api/docker-compose.yml -f /volume1/docker/tools-site/ticket-queue-api/docker-compose.cloudflare.yml down 2>/dev/null || true
$DOCKER compose -f /volume1/docker/openclaw/docker-compose.yml down 2>/dev/null || true

echo "== rename folders =="
rename_dir /volume1/docker/auto-trade /volume1/docker/p3f8c1a2
rename_dir /volume1/docker/receipt-bot /volume1/docker/p91b4e07
rename_dir /volume1/docker/saenggibu /volume1/docker/p2c6d9e1
rename_dir /volume1/docker/saenggibu_backup /volume1/docker/p2c6d9e1-bak
rename_dir /volume1/docker/siyan-upload-api /volume1/docker/p5a0f33c
rename_dir /volume1/docker/works-site /volume1/docker/p8e1b72d
rename_dir /volume1/docker/tools-site /volume1/docker/p6d4a190
rename_dir /volume1/docker/openclaw /volume1/docker/p0c9e4f5
rename_dir /volume1/docker/nodejs-dev /volume1/docker/p7a2b11c
rename_dir /volume1/docker/ticket-queue-api.pre-git /volume1/docker/p6d4a190-pre

echo "== patch compose container/image names =="
# receipt
if [ -f /volume1/docker/p91b4e07/docker-compose.yml ]; then
  sed -i 's/container_name: receipt-bot/container_name: p91b4e07-w1/' /volume1/docker/p91b4e07/docker-compose.yml
  sed -i 's|image: receipt-bot:latest|image: p91b4e07-w1:latest|' /volume1/docker/p91b4e07/docker-compose.yml
  $DOCKER tag receipt-bot:latest p91b4e07-w1:latest 2>/dev/null || true
fi

# saenggibu
if [ -f /volume1/docker/p2c6d9e1/docker-compose.yml ]; then
  sed -i 's/container_name: saenggibu-api/container_name: p2c6d9e1-w1/' /volume1/docker/p2c6d9e1/docker-compose.yml
  sed -i 's/container_name: saenggibu-gateway/container_name: p2c6d9e1-w2/' /volume1/docker/p2c6d9e1/docker-compose.yml
fi
if [ -f /volume1/docker/p2c6d9e1/docker-compose.cloudflare.yml ]; then
  sed -i 's/container_name: saenggibu-tunnel/container_name: p2c6d9e1-w3/' /volume1/docker/p2c6d9e1/docker-compose.cloudflare.yml
fi
$DOCKER tag saenggibu-sgb-api:latest p2c6d9e1-w1:latest 2>/dev/null || true

# siyan
if [ -f /volume1/docker/p5a0f33c/docker-compose.yml ]; then
  sed -i 's/container_name: siyan-upload-api/container_name: p5a0f33c-w1/' /volume1/docker/p5a0f33c/docker-compose.yml
  $DOCKER tag siyan-upload-api-api:latest p5a0f33c-w1:latest 2>/dev/null || true
fi

# works
if [ -f /volume1/docker/p8e1b72d/api/docker-compose.yml ]; then
  sed -i 's/container_name: works-api/container_name: p8e1b72d-w1/' /volume1/docker/p8e1b72d/api/docker-compose.yml
  sed -i 's/container_name: conti-collab/container_name: p8e1b72d-w2/' /volume1/docker/p8e1b72d/api/docker-compose.yml
  $DOCKER tag api-works-api:latest p8e1b72d-w1:latest 2>/dev/null || true
  $DOCKER tag api-conti-collab:latest p8e1b72d-w2:latest 2>/dev/null || true
fi

# ticket-queue
TQ=/volume1/docker/p6d4a190/ticket-queue-api
if [ -f "$TQ/docker-compose.yml" ]; then
  sed -i 's/container_name: ticket-queue-redis/container_name: p6d4a190-w2/' "$TQ/docker-compose.yml"
  sed -i 's/container_name: ticket-queue-api/container_name: p6d4a190-w1/' "$TQ/docker-compose.yml"
  $DOCKER tag ticket-queue-api-api:latest p6d4a190-w1:latest 2>/dev/null || true
fi
if [ -f "$TQ/docker-compose.cloudflare.yml" ]; then
  sed -i 's/container_name: ticket-queue-tunnel/container_name: p6d4a190-w3/' "$TQ/docker-compose.cloudflare.yml"
fi

# openclaw
if [ -f /volume1/docker/p0c9e4f5/docker-compose.yml ]; then
  sed -i 's/container_name: openclaw/container_name: p0c9e4f5-w1/' /volume1/docker/p0c9e4f5/docker-compose.yml
fi

echo "== bring stacks back =="
if [ -f /volume1/docker/p3f8c1a2/docker-compose.nas.yml ]; then
  $DOCKER compose -p p3f8c1a2 -f /volume1/docker/p3f8c1a2/docker-compose.nas.yml --profile tunnel up -d --build
fi
if [ -f /volume1/docker/p91b4e07/docker-compose.yml ]; then
  $DOCKER compose -f /volume1/docker/p91b4e07/docker-compose.yml up -d
fi
if [ -f /volume1/docker/p2c6d9e1/docker-compose.yml ]; then
  if [ -f /volume1/docker/p2c6d9e1/docker-compose.cloudflare.yml ]; then
    $DOCKER compose -f /volume1/docker/p2c6d9e1/docker-compose.yml -f /volume1/docker/p2c6d9e1/docker-compose.cloudflare.yml up -d
  else
    $DOCKER compose -f /volume1/docker/p2c6d9e1/docker-compose.yml up -d
  fi
fi
if [ -f /volume1/docker/p5a0f33c/docker-compose.yml ]; then
  $DOCKER compose -f /volume1/docker/p5a0f33c/docker-compose.yml up -d
fi
if [ -f /volume1/docker/p8e1b72d/api/docker-compose.yml ]; then
  $DOCKER compose -f /volume1/docker/p8e1b72d/api/docker-compose.yml up -d
fi
if [ -f "$TQ/docker-compose.yml" ]; then
  if [ -f "$TQ/docker-compose.cloudflare.yml" ]; then
    $DOCKER compose -f "$TQ/docker-compose.yml" -f "$TQ/docker-compose.cloudflare.yml" up -d
  else
    $DOCKER compose -f "$TQ/docker-compose.yml" up -d
  fi
fi
if [ -f /volume1/docker/p0c9e4f5/docker-compose.yml ]; then
  $DOCKER compose -f /volume1/docker/p0c9e4f5/docker-compose.yml up -d
fi

# Drop obvious markdown at trade root (keeps code; reduces casual browsing signal)
if [ -d /volume1/docker/p3f8c1a2 ]; then
  rm -f /volume1/docker/p3f8c1a2/AGENTS.md /volume1/docker/p3f8c1a2/README.md /volume1/docker/p3f8c1a2/SECURITY.md /volume1/docker/p3f8c1a2/SECURITY.md
fi

echo "== final docker ps =="
$DOCKER ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
echo "== folders =="
ls -1 /volume1/docker
