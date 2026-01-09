# Makefile for Stage0 Runbook API
# Simple curl-based commands for testing runbooks

.PHONY: help dev down open validate execute get-token api container

# Configuration
API_URL ?= http://localhost:8083
RUNBOOK ?= 
ENV ?= 

help:
	@echo "Available commands:"
	@echo "  make dev              - Start API in dev mode with local runbooks mounted"
	@echo "  make down             - Stop all services"
	@echo "  make open             - Open web UI in browser"
	@echo "  make validate         - Validate a runbook (requires RUNBOOK=path/to/runbook.md)"
	@echo "  make execute          - Execute a runbook (requires RUNBOOK=path/to/runbook.md)"
	@echo "  make api              - Start API server (long-running, for development)"
	@echo "  make container        - Build the container image"
	@echo ""
	@echo "Examples:"
	@echo "  make dev"
	@echo "  make validate RUNBOOK=samples/runbooks/SimpleRunbook.md"
	@echo "  make execute RUNBOOK=samples/runbooks/SimpleRunbook.md ENV='TEST_VAR=test_value'"

dev:
	@echo "Starting Stage0 Runbook API in dev mode..."
	@docker-compose -f docker-compose.yaml up -d
	@echo "Waiting for API to be ready..."
	@timeout 30 bash -c 'until curl -sf http://localhost:8083/metrics > /dev/null; do sleep 1; done' || true
	@echo "API is ready at http://localhost:8083"
	@echo "Web UI is available at http://localhost:8084"

down:
	@docker-compose -f docker-compose.yaml down

open:
	@echo "Opening web UI..."
	@open http://localhost:8084 2>/dev/null || xdg-open http://localhost:8084 2>/dev/null || echo "Please open http://localhost:8084 in your browser"

get-token:
	@curl -s -X POST $(API_URL)/dev-login \
		-H "Content-Type: application/json" \
		-d '{"subject": "dev-user", "roles": ["developer", "admin"]}' \
		| jq -r '.access_token // .token // empty'

validate:
	@if [ -z "$(RUNBOOK)" ]; then \
		echo "Error: RUNBOOK is required. Example: make validate RUNBOOK=samples/runbooks/SimpleRunbook.md"; \
		exit 1; \
	fi
	@echo "Validating $(RUNBOOK)..."
	@TOKEN=$$(make -s get-token); \
	if [ -z "$$TOKEN" ]; then \
		echo "Error: Failed to get authentication token. Is the API running?"; \
		exit 1; \
	fi; \
	FILENAME=$$(basename $(RUNBOOK)); \
	if [ -n "$(ENV)" ]; then \
		QUERY="?$$(echo '$(ENV)' | sed 's/ /\\&/g')"; \
	else \
		QUERY=""; \
	fi; \
	curl -s -X PATCH "$(API_URL)/api/runbooks/$$FILENAME$$QUERY" \
		-H "Authorization: Bearer $$TOKEN" \
		-H "Content-Type: application/json" \
		| jq '.' || cat

execute:
	@if [ -z "$(RUNBOOK)" ]; then \
		echo "Error: RUNBOOK is required. Example: make execute RUNBOOK=samples/runbooks/SimpleRunbook.md"; \
		exit 1; \
	fi
	@echo "Executing $(RUNBOOK)..."
	@TOKEN=$$(make -s get-token); \
	if [ -z "$$TOKEN" ]; then \
		echo "Error: Failed to get authentication token. Is the API running?"; \
		exit 1; \
	fi; \
	FILENAME=$$(basename $(RUNBOOK)); \
	if [ -n "$(ENV)" ]; then \
		QUERY="?$$(echo '$(ENV)' | sed 's/ /\\&/g')"; \
	else \
		QUERY=""; \
	fi; \
	curl -s -X POST "$(API_URL)/api/runbooks/$$FILENAME$$QUERY" \
		-H "Authorization: Bearer $$TOKEN" \
		-H "Content-Type: application/json" \
		| jq '.' || cat

# Run the API server (long-running, for development)
api:
	@$(MAKE) down || true
	@echo "Starting API server container..."
	@docker-compose -f docker-compose.yaml up

# Build the deployment container
container:
	@docker build -t ghcr.io/agile-learning-institute/stage0_runbook_api:latest .
