#!/usr/bin/env bash
# Idempotent bootstrap for Cursor Cloud Agents / Automations.
# Runs from .cursor/environment.json "install". Safe to re-run on cached VMs.
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

if ! command -v upbit-strategy-toolkit >/dev/null 2>&1; then
  uv tool install \
    --from git+https://github.com/upbit-official/upbit-strategy-toolkit.git \
    upbit-strategy-toolkit
fi

# Smoke only — do not reinstall.
uv --version
upbit-strategy-toolkit --help >/dev/null
