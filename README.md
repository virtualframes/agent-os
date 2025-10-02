# agent-os

A multi-agent operating system built on the Agent-OS Codex Fabric v2.5 protocol, providing runtime execution, audit compliance, and distributed AI agent orchestration.

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (for local development)
- NATS server (or use Docker Compose setup)
- PostgreSQL 15+ (or use Docker Compose setup)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start local development environment (includes NATS, PostgreSQL, and all services)
make local-dev

# Or install system-wide dependencies manually
pip install pexpect fastapi uvicorn nats-py databases asyncpg
```

## Architecture

### Runtime Execution Layer (`core/`)

Production-ready building blocks for running code directly from the Agent-OS terminal interface:

* **`core/executor.py`** – Streams output from subprocesses spawned with PTY
  support so interactive programs behave exactly like they do in a real
  terminal. Supports Python, JavaScript/TypeScript, Rust, Go, Bash, Lua,
  Ruby, and PHP out of the box.
* **`core/shell.py`** – Maintains a persistent shell session (default `bash`) that
  keeps environment state between commands, ideal for task runners and
  long-lived workflows.
* **`core/repl.py`** – Provides reusable REPL sessions for Python, Node, and Lua
  so multi-step evaluations can share interpreter state.

All components are asyncio-native, enabling responsive text UIs and agent
pipelines.

### Audit & Compliance Services

Agent-OS ships with an append-only audit pipeline to satisfy the
"total traceability" mandate:

* **`services/audit_service/`** – Subscribes to the `agent-os.>` NATS
  wildcard and stores every `Event` payload inside the `audit_events` table.
  The schema is documented inline to aid migrations; persisted entries include
  the original producer timestamp, the source component, and a JSONB payload.
* **`agents/pfc_agent/`** – Pre-Flight Check agent that wraps the
  repository test suite, publishing `EventType` transitions (`pfc.started`,
  `pfc.test_failed`, `pfc.certified`) as it executes. Downstream consumers can
  reconstruct the full pre-merge story using the shared `trace_id`.

Both components rely on the shared `common.protocol.Event` definitions, making
the audit rail contractually identical across services.

### Agent Layer

* **`agents/jules_prototype/`** – AI agent prototype for handling code generation,
  refactoring, and general queries via the NATS message bus
* **`agents/pfc_agent/`** – Pre-Flight Check agent for automated testing and
  certification before merges

### Service Layer

* **`api_gateway/`** – Primary entry point for terminal interface, handles job
  requests and routes them to appropriate agents
* **`token_optimizer/`** – Manages token usage optimization and resource allocation
* **`services/audit_service/`** – Event logging and compliance tracking

### Shared Protocol (`common/`)

* **`common/protocol.py`** – Canonical message structures for NATS bus communication:
  - `JobRequest` / `JobResult` for agent task coordination
  - `Event` / `EventType` for audit trail
  - MessagePack serialization for efficiency

## Development

### Makefile Commands

```bash
# Show all available commands
make help

# Local development
make local-dev          # Start all services with Docker Compose
make stop-local         # Stop all services

# Code quality
make lint               # Run black and flake8
make test               # Run pytest suite

# Infrastructure
make deploy-infra       # Deploy to AWS with Terraform
make destroy-infra      # Tear down AWS infrastructure
```

### CI/CD

GitHub Actions workflow (`.github/workflows/build-and-test.yml`) automatically:
- Checks for merge conflicts with base branch
- Runs linting (black, flake8)
- Executes test suite
- Validates on Python 3.11

### Project Structure

```
agent-os/
├── .github/
│   ├── copilot-instructions.md    # Codex Fabric v2.5 protocol
│   └── workflows/
│       └── build-and-test.yml     # CI/CD pipeline
├── agents/                         # AI agent implementations
│   ├── jules_prototype/
│   └── pfc_agent/
├── api_gateway/                    # Entry point service
├── common/                         # Shared protocol definitions
│   └── protocol.py
├── core/                           # Runtime execution utilities
│   ├── executor.py
│   ├── shell.py
│   └── repl.py
├── services/                       # Background services
│   └── audit_service/
├── terraform/                      # Infrastructure as code
│   └── main.tf
├── token_optimizer/                # Resource management
├── docker-compose.yml              # Local development environment
├── Makefile                        # Development automation
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Protocol Version

This repository follows the **Agent-OS Codex Fabric v2.5** protocol with:
- Six-phase development workflow (Synthesis → Verification → Refinement → Integration → Certification → Iteration)
- Mandatory audit event tracking with `trace_id`
- Multi-LLM routing (GPT-4o, Claude 3.5, Gemini 2.5)
- PR Sentinel feedback loop for iterative refinement

See `.github/copilot-instructions.md` for complete protocol specification.

## Contributing

1. Follow the Phase Protocol defined in `.github/copilot-instructions.md`
2. Ensure code passes linting: `make lint`
3. Add tests for new functionality
4. Update CHANGELOG.md with your changes
5. Emit audit events for significant operations

## License

See LICENSE file for details.
