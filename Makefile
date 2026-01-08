.PHONY: validate execute api down container

# Default runbook filename (relative to samples/runbooks)
RUNBOOK ?= SimpleRunbook.md

# API port (default 8083)
API_PORT ?= 8083

# Extract runbook filename from RUNBOOK path
RUNBOOK_FILENAME := $(shell basename $(RUNBOOK))

# Down target - stops docker-compose services
down:
	@docker-compose -f docker-compose.cli.yaml down > /dev/null 2>&1 || true
	@docker-compose -f docker-compose.cli.yaml rm -f > /dev/null 2>&1 || true

# Helper to wait for API health
_wait_for_api:
	@timeout=30; \
	while [ $$timeout -gt 0 ]; do \
		if curl -sf http://localhost:$(API_PORT)/metrics > /dev/null 2>&1; then \
			echo "API is healthy"; \
			exit 0; \
		fi; \
		sleep 1; \
		timeout=$$((timeout-1)); \
	done; \
	echo "ERROR: API did not become healthy in time"; \
	exit 1

# Helper to get auth token
_get_token:
	@curl -s -X POST http://localhost:$(API_PORT)/dev-login \
		-H "Content-Type: application/json" \
		-d '{"subject":"cli-user","roles":["developer","admin"]}' | \
		python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))"

# Validate runbook using API via docker-compose
validate:
	@$(MAKE) down || true
	@echo "Starting API server..."
	@docker-compose -f docker-compose.cli.yaml up -d
	@sleep 3
	@$(MAKE) _wait_for_api || ($(MAKE) down && exit 1)
	@echo "Getting authentication token..."
	@TOKEN=$$($(MAKE) _get_token); \
	if [ -z "$$TOKEN" ]; then \
		echo "ERROR: Failed to get authentication token"; \
		$(MAKE) down; \
		exit 1; \
	fi; \
	echo "Validating runbook $(RUNBOOK_FILENAME)..."; \
	RESPONSE=$$(curl -s -w "\n%{http_code}" -X PATCH "http://localhost:$(API_PORT)/api/runbooks/$(RUNBOOK_FILENAME)/validate" \
		-H "Authorization: Bearer $$TOKEN" \
		-H "Content-Type: application/json"); \
	HTTP_CODE=$$(echo "$$RESPONSE" | tail -n1); \
	BODY=$$(echo "$$RESPONSE" | sed '$$d'); \
	if [ "$$HTTP_CODE" -eq 200 ]; then \
		echo "$$BODY" | python3 -m json.tool; \
		SUCCESS=$$(echo "$$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))"); \
		if [ "$$SUCCESS" = "True" ]; then \
			echo "✓ Runbook validation passed: $(RUNBOOK_FILENAME)"; \
		else \
			echo "✗ Runbook validation failed: $(RUNBOOK_FILENAME)"; \
			echo "$$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"ERROR: {e}\") for e in data.get('errors', [])]; [print(f\"WARNING: {w}\") for w in data.get('warnings', [])]"; \
			curl -s -X POST "http://localhost:$(API_PORT)/api/shutdown" -H "Authorization: Bearer $$TOKEN" > /dev/null 2>&1 || true; \
			sleep 1; \
			$(MAKE) down; \
			exit 1; \
		fi; \
	else \
		echo "ERROR: Validation request failed with HTTP $$HTTP_CODE"; \
		echo "$$BODY"; \
		curl -s -X POST "http://localhost:$(API_PORT)/api/shutdown" -H "Authorization: Bearer $$TOKEN" > /dev/null 2>&1 || true; \
		sleep 1; \
		$(MAKE) down; \
		exit 1; \
	fi; \
	echo "Shutting down API server..."; \
	curl -s -X POST "http://localhost:$(API_PORT)/api/shutdown" -H "Authorization: Bearer $$TOKEN" > /dev/null 2>&1 || true; \
	sleep 1; \
	$(MAKE) down

# Execute runbook using API via docker-compose
execute:
	@$(MAKE) down || true
	@echo "Starting API server..."
	@docker-compose -f docker-compose.cli.yaml up -d
	@sleep 3
	@$(MAKE) _wait_for_api || ($(MAKE) down && exit 1)
	@echo "Getting authentication token..."
	@TOKEN=$$($(MAKE) _get_token); \
	if [ -z "$$TOKEN" ]; then \
		echo "ERROR: Failed to get authentication token"; \
		$(MAKE) down; \
		exit 1; \
	fi; \
	echo "Executing runbook $(RUNBOOK_FILENAME)..."; \
	ENV_BODY="{}"; \
	if [ -n "$(ENV_VARS)" ]; then \
		ENV_BODY=$$(python3 -c "import sys, json; env_dict={}; [env_dict.update({k:v}) for k,v in [p.split('=',1) for p in sys.argv[1].split() if '=' in p]]; print(json.dumps({'env_vars': env_dict}))" "$(ENV_VARS)"); \
	fi; \
	RESPONSE=$$(curl -s -w "\n%{http_code}" -X POST "http://localhost:$(API_PORT)/api/runbooks/$(RUNBOOK_FILENAME)/execute" \
		-H "Authorization: Bearer $$TOKEN" \
		-H "Content-Type: application/json" \
		-d "$$ENV_BODY"); \
	HTTP_CODE=$$(echo "$$RESPONSE" | tail -n1); \
	BODY=$$(echo "$$RESPONSE" | sed '$$d'); \
	if [ "$$HTTP_CODE" -eq 200 ]; then \
		echo "$$BODY" | python3 -m json.tool; \
		SUCCESS=$$(echo "$$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))"); \
		RETURN_CODE=$$(echo "$$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('return_code', 1))"); \
		if [ "$$SUCCESS" = "True" ] && [ "$$RETURN_CODE" -eq 0 ]; then \
			echo "✓ Runbook execution succeeded: $(RUNBOOK_FILENAME)"; \
		else \
			echo "✗ Runbook execution failed: $(RUNBOOK_FILENAME) (return code: $$RETURN_CODE)"; \
			curl -s -X POST "http://localhost:$(API_PORT)/api/shutdown" -H "Authorization: Bearer $$TOKEN" > /dev/null 2>&1 || true; \
			sleep 1; \
			$(MAKE) down; \
			exit $$RETURN_CODE; \
		fi; \
	else \
		echo "ERROR: Execution request failed with HTTP $$HTTP_CODE"; \
		echo "$$BODY"; \
		curl -s -X POST "http://localhost:$(API_PORT)/api/shutdown" -H "Authorization: Bearer $$TOKEN" > /dev/null 2>&1 || true; \
		sleep 1; \
		$(MAKE) down; \
		exit 1; \
	fi; \
	echo "Shutting down API server..."; \
	curl -s -X POST "http://localhost:$(API_PORT)/api/shutdown" -H "Authorization: Bearer $$TOKEN" > /dev/null 2>&1 || true; \
	sleep 1; \
	$(MAKE) down

# Run the API server (long-running, for development)
api:
	@$(MAKE) down || true
	@echo "Starting API server container..."
	@docker-compose -f docker-compose.cli.yaml up

# Build the deployment container
container:
	docker build -t ghcr.io/agile-learning-institute/stage0_runbook_api:latest .
