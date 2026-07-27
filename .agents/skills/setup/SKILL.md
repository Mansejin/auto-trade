---
name: setup
description: Diagnose the current mode and CLI availability when using upbit-strategy-toolkit for the first time or when another skill cannot run. Checks uv/uvx behavior in clone mode and agent skills mode. Environment setup, getting started, first use, setup, uv explanation. Use when the user is starting for the first time, or when another skill detects unmet environment requirements (missing uv, uv sync failure, CLI execution failure, etc.) and recommends routing here.
compatibility: macOS / Linux / Windows. Requires curl(macOS/Linux) or PowerShell(Windows), network access
metadata:
  version: "v0.8.1"
  author: "Upbit"
---

# setup

Identify the upbit-strategy-toolkit usage mode and diagnose whether the CLI can run in the current environment. This skill is **a mode-detection and diagnostic utility**, not installation automation. `create-strategy` and `backtest` handle strategy creation and backtesting.

OS-specific installation instructions for cases where uv is missing are split into references/:
- uv installation reference: [references/uv-install.md](references/uv-install.md)

---

## Triggers

- "Use it for the first time"
- "How do I set up the environment?"
- "What is uv? / It says uv is missing"
- Another skill (create-strategy/backtest) detected unmet environment requirements (missing uv, `uv sync` failure, CLI execution failure, etc.) and recommended routing here

> **Automatic routing recommendation**: if create-strategy / backtest fails to run the wrapper on its first call, recommend setup.

## Routing Contract

- Role: environment diagnosis and recovery entry point
- Next step: `create-strategy`
- Recovery entry: guide to this skill when `create-strategy` or `backtest` detects missing uv, `uv sync` failure, or CLI execution failure
- Out of scope: this skill does not handle strategy design, backtest interpretation, or market-rule work

## Do Not

- **Do not change the user's system Python arbitrarily** - uv isolates the required version in a virtual environment. Do not guide the user to upgrade/downgrade system Python.
- **Do not recommend `pip install -g`** - clone-mode dependencies stay inside the virtual environment through `uv sync`.
- **Do not connect to live trading** - see [Live Trading Guardrail](#live-trading-guardrail).

---

## Workflow

Check pass/fail for each item before moving to the next. On failure, report as factual statements which command failed and what error occurred.

```
setup

[ ] 1. Identify usage mode
[ ] 2. Check uv installation
[ ] 3. Run mode-specific CLI diagnostics
```

### 1. Identify Usage Mode

Check whether the current workspace is the upbit-strategy-toolkit repo.

| Mode | Detection | Default data root (used unless `config set data-dir` was run) |
|---|---|---|
| clone mode | Current cwd or an ancestor has `name = "upbit-strategy-toolkit"` in `pyproject.toml` and `upbit_strategy_toolkit/` | The current working directory at run time |
| agent skills mode (global) | Skill was installed with `npx skills add ... -g`; the wrapper script's own path sits directly under `$HOME/.claude/skills`, `$HOME/.agents/skills`, or `$HOME/.cursor/skills` | The current working directory at run time |
| agent skills mode (project-scoped) | Skill was installed with `npx skills add ...` (no `-g`); the wrapper script's own path does not sit under the home-directory skills paths above, and the current workspace does not contain the upbit-strategy-toolkit repo | The current working directory at run time |

When neither `UPBIT_TOOLKIT_DATA_DIR` nor a stored `config set data-dir` value is present, the CLI resolves the data root to the current working directory at run time, regardless of mode. If the user has run `config set data-dir`, that stored value is used instead. Report the resolved value with `config get data-dir` rather than assuming it from the mode table above.

### 2. Check uv Installation

```bash
uv --version
```

If it prints normally, this passes. If uv is missing, point to [references/uv-install.md](references/uv-install.md), then check `uv --version` again after installation.

### 3-A. Clone Mode Diagnostics

Run from the repo workspace/cwd.

```bash
uv sync
uv run upbit-strategy-toolkit --help
```

`uv sync` creates `.venv/` and prepares the required Python and dependencies. Clone mode diagnostics pass when `uv run upbit-strategy-toolkit --help` prints help.

On failure, report factual details: which package failed and what error occurred. Do not bypass with arbitrary `pip install`.

### 3-B. Agent Skills Mode (Global or Project) Diagnostics

When the repo is not cloned, check by running the CLI directly from the GitHub source. This step is the same for global and project-scoped installs.

```bash
uvx --from git+https://github.com/upbit-official/upbit-strategy-toolkit.git upbit-strategy-toolkit --help
```

Agent skills mode diagnostics pass when help is printed. On failure, report based on the original error whether it is missing uv, GitHub access failure, or Python 3.12 acquisition failure.

---

## Bidirectional Handoff

### After Setup Completion -> create-strategy

When diagnostics pass, naturally hand off to the next skill with this line:

```
upbit-strategy-toolkit CLI diagnostics complete. You can now create a strategy.

Next step: create-strategy skill
- Start with natural language such as "Create a golden cross strategy".
- The generated {data_root}/strategies/{slug}.json can be validated with the backtest skill.
```

### Blocked During Setup -> Factual Report

Without judging good/bad, state exactly which step produced which error:

```
[Step 2 blocked] `uv --version` returned "command not found"
-> Shell restart or PATH check is required (see references/uv-install.md)
```

```
[clone mode Step 3 blocked] pandas wheel build failed during `uv sync`
Original error: ...
-> Recheck Python 3.12+ availability. If system Python is 3.11 or lower, run `uv python install 3.12` and retry.
```

```
[agent skills mode Step 3 blocked] GitHub access failed during `uvx --from ... upbit-strategy-toolkit --help`
Original error: ...
-> Network or GitHub access permissions need to be checked.
```

---

## Live Trading Guardrail

Same policy as create-strategy / backtest. Reject live-trading integration requests even during setup.

**Response template**: If the user's message is in Korean, use the Korean version; otherwise use the English version.

Korean:
```text
이 도구는 백테스트(과거 데이터 시뮬레이션) 전용입니다.
실전 매매가 필요하다면 [upbit-agent-skills](https://github.com/upbit-official/upbit-agent-skills)를 이용해주세요.

setup 스킬은 백테스트 환경 설정만 지원합니다.
```

English:
```text
This tool is for backtesting (historical data simulation) only.
Use the separate [upbit-agent-skills](https://github.com/upbit-official/upbit-agent-skills) tool for live trading.

The setup skill only supports backtest environment setup.
```

---

## Execution Rule Summary

- Identify the mode first, then run only that mode's diagnostic commands
- clone mode: `uv --version`, `uv sync`, `uv run upbit-strategy-toolkit --help`
- agent skills mode (global or project-scoped): `uv --version`, `uvx --from git+https://github.com/upbit-official/upbit-strategy-toolkit.git upbit-strategy-toolkit --help`
- Do not guide changes to system Python - uv isolates it in a virtual environment
- Report failures only as factual statements (step + command + original error)
- Naturally hand off to create-strategy after setup completes
- Refuse live trading requests and point to [upbit-agent-skills](https://github.com/upbit-official/upbit-agent-skills)
