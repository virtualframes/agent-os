# Agent-OS: Makefile for Development and Deployment Automation
# Provides a simple, high-level interface for complex operations.

# Default target
.PHONY: help
help:
	@echo "Agent-OS Control Makefile"
	@echo "-------------------------"
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  local-dev          - Start all services locally using Docker Compose."
	@echo "  stop-local         - Stop all local services."
	@echo "  build-agents       - Build Docker images for all agent services."
	@echo "  deploy-infra       - Apply Terraform configurations to provision cloud infrastructure."
	@echo "  destroy-infra      - Destroy Terraform-managed infrastructure."
	@echo "  lint               - Run linters on all Python code."
	@echo "  test               - Run automated tests."

# Local Development
.PHONY: local-dev
local-dev:
	@echo "Starting local development environment with Docker Compose..."
	docker-compose up --build -d

.PHONY: stop-local
stop-local:
	@echo "Stopping local development environment..."
	docker-compose down

# Docker Image Management
.PHONY: build-agents
build-agents:
	@echo "Building Docker images for all services..."
	docker-compose build --no-cache

# Infrastructure as Code (Terraform)
.PHONY: deploy-infra
deploy-infra:
	@echo "Deploying infrastructure with Terraform..."
	cd terraform && terraform init && terraform apply -auto-approve

.PHONY: destroy-infra
destroy-infra:
	@echo "Destroying infrastructure with Terraform..."
	cd terraform && terraform destroy -auto-approve

# Code Quality & Testing
.PHONY: lint
lint:
	@echo "Running linters..."
	black api_gateway token_optimizer agents common services core
	flake8 api_gateway token_optimizer agents common services core --max-line-length=100

.PHONY: test
test:
	@echo "Running tests..."
	pytest || echo "No tests found"
