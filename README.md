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

## Core System Scaffolding

The repository now includes skeleton implementations for the long-lived
components referenced in the Agent-OS specification:

* `core/quantum_router.py` – adaptive routing logic that selects the best agent
  for a command while emitting audit events via the shared logger.
* `core/graph_engine.py` – deterministic, color-aware spacetime graph builder
  backed by in-memory Neo4j and vector store adapters.
* `core/terminal_engine.py` – Textual-based UI scaffold that wires the router
  and graph together. It degrades gracefully when Textual is not installed.
* `db/` – lightweight stand-ins for the audit log, Neo4j adapter, and vector
  store APIs so higher layers can be developed without external services.
* `integrations/xbow_scanner.py` – placeholder HackerOne integration that keeps
  the interface stable for future vulnerability ingestion.

## Audit & Compliance Services

Agent-OS now ships with an append-only audit pipeline to satisfy the
"total traceability" mandate:

* `services/audit_service/main.py` – subscribes to the `agent-os.>` NATS
  wildcard and stores every `Event` payload inside the `audit_events` table.
  The schema is documented inline to aid migrations; persisted entries include
  the original producer timestamp, the source component, and a JSONB payload.
* `agents/pfc_agent/main.py` – upgraded Pre-Flight Check agent that wraps the
  repository test suite, publishing `EventType` transitions (`pfc.started`,
  `pfc.test_failed`, `pfc.certified`) as it executes. Downstream consumers can
  reconstruct the full pre-merge story using the shared `trace_id`.

Both components rely on the shared `common.protocol.Event` definitions, making
the audit rail contractually identical across services.

## Dependencies

Local development now requires `numpy` for the vector store utilities and
`textual` to render the optional terminal UI. Install extras with:

```bash
pip install numpy textual
```
