.PHONY: validate execute api down container

# Default runbook path
RUNBOOK ?= ./samples/runbooks/SimpleRunbook.md

# API port (default 8083)
API_PORT ?= 8083

# Validate runbook using the deployment container
validate:
	docker run --rm \
		-v $(PWD):/workspace \
		-w /workspace \
		-e RUNBOOK=$(RUNBOOK) \
		$(ENV_VARS) \
		ghcr.io/agile-learning-institute/stage0_runbook_api:latest \
		runbook validate --runbook $(RUNBOOK)

# Execute runbook using the deployment container
execute:
	docker run --rm \
		-v $(PWD):/workspace \
		-w /workspace \
		-e RUNBOOK=$(RUNBOOK) \
		$(ENV_VARS) \
		ghcr.io/agile-learning-institute/stage0_runbook_api:latest \
		runbook execute --runbook $(RUNBOOK)

# Run the API server (restarts if already running)
api: down
	@echo "Starting API server container..."
	@docker run -d --rm \
		--name stage0_runbook_api \
		-v $(PWD)/samples/runbooks:/workspace \
		-w /workspace \
		-p $(API_PORT):$(API_PORT) \
		-e API_PORT=$(API_PORT) \
		-e RUNBOOKS_DIR=. \
		ghcr.io/agile-learning-institute/stage0_runbook_api:latest \
		runbook serve --runbooks-dir . --port $(API_PORT) > /dev/null 2>&1 || true
	@sleep 2
	@if docker ps --format '{{.Names}}' | grep -q '^stage0_runbook_api$$'; then \
		echo "API server started. Tailing logs (Ctrl+C to stop)..."; \
		docker logs -f stage0_runbook_api; \
	else \
		echo "ERROR: Container stopped immediately. Last logs:"; \
		docker logs stage0_runbook_api 2>/dev/null || echo "No logs available"; \
		exit 1; \
	fi

# Stop and remove the API server container
down:
	@docker stop stage0_runbook_api 2>/dev/null || true
	@echo "API server stopped"

# Build the deployment container
container:
	docker build -t ghcr.io/agile-learning-institute/stage0_runner:latest .

