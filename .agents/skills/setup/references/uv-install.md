# uv Installation

upbit-strategy-toolkit uses [astral-sh/uv](https://docs.astral.sh/uv/) as its virtual environment and dependency management tool. uv automatically downloads the Python version required by `pyproject.toml` and creates an isolated environment, independent of system Python.

Use this document only when `uv` itself is missing. Global installation of the upbit-strategy-toolkit CLI is not an official usage path, and the setup skill diagnoses whether clone mode and agent skills mode can run; it is not installation automation.

## Version Requirements

upbit-strategy-toolkit's `pyproject.toml` requires:

- **Python**: `>=3.12`
- **Core dependencies**: `pandas>=2.0`, `pydantic>=2.0`, `upbit-sdk>=0.9.0`, `requests`, `typer>=0.25.1`
- **dev group**: `pandas-stubs`, `pre-commit`, `pytest`, `ruff`, `ty`

uv can automatically download Python 3.12+ even when the system does not have it (`uv python install 3.12`).

## OS-Specific Installation

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Alternative Installation (Optional)

If one of these tools is already available, it can be used instead:

- macOS Homebrew: `brew install uv`
- pipx: `pipx install uv`
- WinGet: `winget install --id=astral-sh.uv -e`

## Check After Installation

```bash
uv --version
```

Passes when output looks like `uv 0.x.y`.

## Restart Shell

If `uv: command not found` appears immediately after installation:

1. Open a new terminal window (refresh PATH)
2. Or refresh PATH in the current shell:
   - bash/zsh: `source ~/.bashrc` or `source ~/.zshrc`
   - PowerShell: new window

The installation script usually installs uv to `~/.local/bin` (macOS/Linux) or `%USERPROFILE%\.local\bin` (Windows) and adds it to PATH.

## Next Step

When `uv --version` prints normally, return to the setup skill and run the diagnostic commands for the current usage mode.

clone mode:

```bash
uv sync
uv run upbit-strategy-toolkit --help
```

agent skills mode:

```bash
uvx --from git+https://github.com/upbit-official/upbit-strategy-toolkit.git upbit-strategy-toolkit --help
```

`uv sync` and `uvx` prepare the required Python 3.12+ in uv's managed area and do not change system Python.

## Troubleshooting

| Symptom | Cause / Response |
|---|---|
| `command not found: uv` | Restart shell or check PATH (whether `echo $PATH` includes `~/.local/bin`) |
| `uv sync` stalls during Python download | Check network / company proxy. A mirror can be specified with the `UV_PYTHON_INSTALL_MIRROR` environment variable |
| `pandas` wheel build failure | Rare (uv usually uses prebuilt wheels). If it occurs, report the user's OS and architecture |
| company security network blocks install.sh | Bypass through Homebrew / pipx path |
