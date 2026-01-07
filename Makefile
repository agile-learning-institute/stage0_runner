.PHONY: validate execute container

# Default runbook path
RUNBOOK ?= ./samples/runbooks/SimpleRunbook.md

# Validate runbook using the deployment container
validate:
	docker run --rm \
		-v $(PWD):/workspace \
		-w /workspace \
		-e RUNBOOK=$(RUNBOOK) \
		ghcr.io/agile-learning-institute/stage0_runner:latest \
		runbook validate --runbook $(RUNBOOK)

# Execute runbook using the deployment container
execute:
	docker run --rm \
		-v $(PWD):/workspace \
		-w /workspace \
		-e RUNBOOK=$(RUNBOOK) \
		ghcr.io/agile-learning-institute/stage0_runner:latest \
		runbook execute --runbook $(RUNBOOK)

# Build the deployment container
container:
	docker build -t ghcr.io/agile-learning-institute/stage0_runner:latest .

