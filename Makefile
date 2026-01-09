.PHONY: validate execute api up down container

# Default runbook filename (relative to samples/runbooks)
RUNBOOK ?= SimpleRunbook.md

# API port (default 8083)
API_PORT ?= 8083

# Extract runbook filename from RUNBOOK path
RUNBOOK_FILENAME := $(shell basename $(RUNBOOK))

# Path to CLI script
CLI := python3 src/cli/runbook.py
API_URL := http://localhost:$(API_PORT)

# Start the API server using docker-compose
up:
	@echo "Starting API server..."
	@docker-compose -f docker-compose.yaml up -d

# Stop docker-compose services
down:
	@echo "Stopping API server..."
	@docker-compose -f docker-compose.yaml down > /dev/null 2>&1 || true
	@docker-compose -f docker-compose.yaml rm -f > /dev/null 2>&1 || true

# Validate runbook using CLI
validate:
	@$(MAKE) down || true
	@$(MAKE) up
	@$(CLI) --api-url $(API_URL) validate $(RUNBOOK_FILENAME); \
	EXIT_CODE=$$?; \
	echo "Shutting down API server..."; \
	$(CLI) --api-url $(API_URL) --no-wait shutdown > /dev/null 2>&1 || true; \
	sleep 1; \
	$(MAKE) down; \
	exit $$EXIT_CODE

# Execute runbook using CLI
execute:
	@$(MAKE) down || true
	@$(MAKE) up
	@if [ -n "$(ENV_VARS)" ]; then \
		$(CLI) --api-url $(API_URL) execute $(RUNBOOK_FILENAME) --env-vars "$(ENV_VARS)"; \
	else \
		$(CLI) --api-url $(API_URL) execute $(RUNBOOK_FILENAME); \
	fi; \
	EXIT_CODE=$$?; \
	echo "Shutting down API server..."; \
	$(CLI) --api-url $(API_URL) --no-wait shutdown > /dev/null 2>&1 || true; \
	sleep 1; \
	$(MAKE) down; \
	exit $$EXIT_CODE

# Run the API server (long-running, for development)
api:
	@$(MAKE) down || true
	@echo "Starting API server container..."
	@docker-compose -f docker-compose.yaml up

# Build the deployment container
container:
	docker build -t ghcr.io/agile-learning-institute/stage0_runbook_api:latest .
