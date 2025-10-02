# agent-os

## Runtime execution utilities

The `core` package now exposes production-ready building blocks for running
code directly from the Agent-OS terminal interface:

* `core/executor.py` – streams output from subprocesses spawned with PTY
  support so interactive programs behave exactly like they do in a real
  terminal. Supports Python, JavaScript/TypeScript, Rust, Go, Bash, Lua,
  Ruby, and PHP out of the box.
* `core/shell.py` – maintains a persistent shell session (default `bash`) that
  keeps environment state between commands, ideal for task runners and
  long-lived workflows.
* `core/repl.py` – provides reusable REPL sessions for Python, Node, and Lua
  so multi-step evaluations can share interpreter state.

All components are asyncio-native, enabling responsive text UIs and agent
pipelines. Install dependencies with `pip install pexpect` (plus any
language runtimes you wish to execute).
