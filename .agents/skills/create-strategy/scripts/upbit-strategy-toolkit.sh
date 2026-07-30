#!/usr/bin/env bash
set -euo pipefail

export PATH="${HOME}/.local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_upbit_strategy_toolkit_root() {
  local dir="$SCRIPT_DIR"

  while [ "$dir" != "/" ]; do
    if [ -f "$dir/pyproject.toml" ] \
      && [ -d "$dir/upbit_strategy_toolkit" ] \
      && grep -q 'name = "upbit-strategy-toolkit"' "$dir/pyproject.toml"; then
      printf '%s\n' "$dir"
      return 0
    fi

    dir="$(dirname "$dir")"
  done

  return 1
}

if ROOT="$(find_upbit_strategy_toolkit_root)"; then
  CLI=(uv run --project "$ROOT" upbit-strategy-toolkit)
elif command -v upbit-strategy-toolkit >/dev/null 2>&1; then
  # Prefer uv-tool install from scripts/cloud-install.sh (no per-run git fetch).
  CLI=(upbit-strategy-toolkit)
else
  CLI=(uvx --from git+https://github.com/upbit-official/upbit-strategy-toolkit.git upbit-strategy-toolkit)
fi

# Data root resolution is delegated entirely to the CLI (get_data_path):
# env var UPBIT_TOOLKIT_DATA_DIR -> config.json data_dir -> cwd.
exec "${CLI[@]}" "$@"
