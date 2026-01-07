# Stage0 Runbook Runner

This repository contains the `stage0_runner` utility which is used to execute Runbooks. A runbook is a markdown file, with some specific layout requirements, see [RUNBOOK.md](./RUNBOOK.md) for details. 

## Prerequisites
- Python 3.12+
- pipenv (install with `pip install pipenv`)
- Docker (for container-based execution)

## Developer Commands
```sh
# Install dependencies
pipenv install

# Execute the runbook locally
export RUNBOOK=./test/runbooks/SimpleRunbook.md 
pipenv run execute

# Validate the runbook locally
export RUNBOOK=./test/runbooks/SimpleRunbook.md
pipenv run validate

# Build the deployment container
make container

# Validate runbook using the deployment container
RUNBOOK=./test/runbooks/SimpleRunbook.md make validate

# Execute runbook using the deployment container
RUNBOOK=./test/runbooks/SimpleRunbook.md make execute
```

### Validation Processing:
Validation confirms the runbook is well formed and all runtime dependencies are met. Validation is not fail fast, and provides helpful errors that make it easy to fix problems. Validation goes beyond just validating that the file is well formed, it also validates that execution requirements are met. 
- Verify that the Runbook file exists
- Verify the Environment yaml exists
- Verify that the Env Vars listed exist
- Verify that the # File System Requirements header exists
- Verify that the required files / folders exist
- Verify that the runbook has the required sh code block
- Verify that the runbook has a # History Header

## Execution Processing
- Fail fast validate.
- Create temp.zsh with the contents of the code block
- Invoke temp.zsh and capture stdout and stderr
- Append execution information onto Runbook. 
- Remove temp.zsh

## Extending the Base Image

The base `stage0_runner` image is kept minimal and includes only:
- Python 3.12 and pipenv
- zsh (required for runbook scripts)
- The runbook runner utility

For runbooks that need additional tools (like Docker CLI or GitHub CLI), you can extend the base image. A sample extended Dockerfile is provided:

**Dockerfile.extended** - Extends the base image with Docker CLI and GitHub CLI

To use the extended image:
```sh
# Build the extended image
docker build -f Dockerfile.extended -t my-stage0-runner:extended .

# Run with Docker socket mount (for docker commands)
docker run --rm \
    -v $(PWD):/workspace \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -w /workspace \
    -e RUNBOOK=./my-runbook.md \
    my-stage0-runner:extended \
    runbook execute --runbook ./my-runbook.md
```

You can create your own extended Dockerfile based on your specific needs:
```dockerfile
FROM ghcr.io/agile-learning-institute/stage0_runner:latest

# Add your custom tools here
RUN apt-get update && \
    apt-get install -y --no-install-recommends your-tool && \
    rm -rf /var/lib/apt/lists/*
```

## Project Structure
```
.
├── Dockerfile               # Base Docker configuration (minimal)
├── Dockerfile.extended      # Extended image with Docker CLI and GitHub CLI
├── Makefile                 # Make targets for container operations
├── Pipfile                  # Python dependencies (pipenv)
├── README.md                # This file
├── RUNBOOK.md               # Runbook format specification
├── src/
│   ├── command.py          # The runbook command implementation
│   └── runbook              # Wrapper script for simplified usage
└── test/
    ├── test_command.py      # Unit tests for the runner
    └── runbooks/            # Test Runbooks
        ├── SimpleRunbook.md
        ├── CreatePackage.md
        └── CreatePackage.dockerfile
```
