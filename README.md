# agent-os

## Runtime execution utilities

The `core` package now exposes production-ready building blocks for running
code directly from the Agent-OS terminal interface:

* `core/executors/` – plugin-style executors that isolate runtime specifics
  per language (Python, JavaScript/TypeScript, Rust, Go, Bash, Lua, Ruby, PHP).
  The legacy `core/executor.py` facade now routes requests to the registry of
  dedicated executors.
* `core/shells/` – discrete implementations for each supported interactive
  shell (`bash`, `zsh`, etc.) managed via a lightweight `ShellManager`. When a
  shell name is requested that is not pre-registered, the generic shell
  adapter falls back to executing the provided command directly. The former
  `InteractiveShell` class is now a compatibility wrapper.
* `core/repls/` – modular, per-language REPL implementations with a
  high-level `REPLManager` exposed from `core/repl.py`.

All components are asyncio-native, enabling responsive text UIs and agent
pipelines. Install dependencies with `pip install pexpect` (plus any
language runtimes you wish to execute).
