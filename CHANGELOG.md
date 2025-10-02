# Changelog

All notable changes to Agent-OS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflow (`build-and-test.yml`) with automated linting, testing, and merge conflict detection
- Audit & compliance services infrastructure:
  - `services/audit_service/` - NATS-based audit event logging to PostgreSQL
  - `agents/pfc_agent/` - Pre-Flight Check agent with audit event publishing
  - `common/protocol.py` - Shared message protocol for inter-service communication
- Multi-service Docker Compose setup for local development
- Makefile with targets for development, testing, and infrastructure management
- Terraform configuration for cloud infrastructure provisioning
- API Gateway service for terminal interface
- Token Optimizer service with PostgreSQL backend
- Jules prototype agent for AI operations
- `requirements.txt` with all necessary Python dependencies
- Merge conflict detection step in CI workflow to catch conflicts early

### Changed
- Updated `.github/copilot-instructions.md` to Codex Fabric v2.5 protocol with:
  - Six-phase workflow (Synthesis, Verification, Refinement, Integration, Certification, Iteration)
  - Audit & event requirements with trace_id tracking
  - Enhanced coding standards for Python, JS/TS, Shell, Terraform, and Markdown
  - Context & tooling commands documentation
  - PR Sentinel feedback loop integration
- Enhanced `README.md` with comprehensive documentation of:
  - Runtime execution utilities (executor, shell, repl)
  - Audit & compliance services
  - Event-driven architecture components

### Security
- Enforced secure storage patterns for secrets
- Added PostgreSQL authentication for services
- Implemented audit trail for all system events
- Sandboxed execution via Docker containers

## [0.1.0] - 2025-10-02

### Added
- Initial runtime execution utilities:
  - `core/executor.py` - PTY-backed multi-language code execution
  - `core/shell.py` - Persistent interactive shell sessions
  - `core/repl.py` - REPL management for Python, Node, and Lua
- Core Python infrastructure with asyncio support
- Basic documentation in README.md
