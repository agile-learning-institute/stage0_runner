# Makefile for Stage0 Runbook API
# Simple curl-based commands for testing runbooks

.PHONY: help api down open validate execute get-token container

# Configuration
API_URL ?= http://localhost:8083
RUNBOOK ?= 
ENV ?= 

help:
	@echo "Available commands:"
	@echo "  make api              - Start API server with local runbooks mounted (for testing runbooks)"
	@echo "  make down             - Stop all services"
	@echo "  make open             - Open web UI in browser"
	@echo "  make validate         - Validate a runbook (requires RUNBOOK=path/to/runbook.md)"
	@echo "  make execute          - Execute a runbook (requires RUNBOOK=path/to/runbook.md)"
	@echo "  make container        - Build the container image"
	@echo ""
	@echo "Examples:"
	@echo "  make api              # Start API in one terminal"
	@echo "  make validate RUNBOOK=samples/runbooks/SimpleRunbook.md  # In another terminal"
	@echo "  make execute RUNBOOK=samples/runbooks/SimpleRunbook.md ENV='TEST_VAR=test_value'"

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
		ENV_JSON=$$(echo '$(ENV)' | tr ' ' '\n' | awk -F= '{printf "{\"key\":\"%s\",\"value\":\"%s\"}\n", $$1, $$2}' | jq -s 'map({(.key): .value}) | add'); \
		curl -s -X PATCH "$(API_URL)/api/runbooks/$$FILENAME" \
			-H "Authorization: Bearer $$TOKEN" \
			-H "Content-Type: application/json" \
			-d "{\"env_vars\":$$ENV_JSON}" \
			| jq '.' || cat; \
	else \
		curl -s -X PATCH "$(API_URL)/api/runbooks/$$FILENAME" \
			-H "Authorization: Bearer $$TOKEN" \
			-H "Content-Type: application/json" \
			| jq '.' || cat; \
	fi

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
		ENV_JSON=$$(echo '$(ENV)' | tr ' ' '\n' | awk -F= '{printf "{\"key\":\"%s\",\"value\":\"%s\"}\n", $$1, $$2}' | jq -s 'map({(.key): .value}) | add'); \
		curl -s -X POST "$(API_URL)/api/runbooks/$$FILENAME" \
			-H "Authorization: Bearer $$TOKEN" \
			-H "Content-Type: application/json" \
			-d "{\"env_vars\":$$ENV_JSON}" \
			| jq '.' || cat; \
	else \
		curl -s -X POST "$(API_URL)/api/runbooks/$$FILENAME" \
			-H "Authorization: Bearer $$TOKEN" \
			-H "Content-Type: application/json" \
			| jq '.' || cat; \
	fi

# Start API server with local runbooks mounted (for runbook authors)
api:
	@$(MAKE) down || true
	@echo "Starting API server with local runbooks mounted..."
	@docker-compose -f docker-compose.yaml up -d
	@echo "Waiting for API to be ready..."
	@timeout 30 bash -c 'until curl -sf http://localhost:8083/metrics > /dev/null; do sleep 1; done' || true
	@echo "API is ready at http://localhost:8083"
	@echo "Runbooks are mounted from ./samples/runbooks"
	@echo "Use 'make down' to stop the API"

# Build the deployment container
container:
	@docker build -t ghcr.io/agile-learning-institute/stage0_runbook_api:latest .
