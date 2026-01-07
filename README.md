# Stage0 Runbook Runner

This repository contains the `stage0_runner` utility which is used to execute Runbooks. A Runbook is a markdown file that describes a (automated) task. You can create a runbook for a manual task, but for an automated task it must have the proper [Runbook layout](./RUNBOOK.md). Here is an [empty template](./test/runbooks/Runbook.md) runbook, and a [Simple Example](./test/runbooks/SimpleRunbook.md) runbook. 

## Quick Start
See the [Makefile](./Makefile) for examples of using the utility container to validate or execute a Runbook.

## Contributing Prerequisites
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

## SRE Guidance
You can extend the Base Image to create a custom runbook runner container that includes additional script prerequisites such as a vendor CLI (GitHub, AWS, ...). You can even package a set of "approved" RunBooks with that container. 

The base `stage0_runner` image is kept minimal and includes only:
- Python 3.12 and pipenv
- zsh (required for runbook scripts)
- The runbook runner utility

For runbooks that need additional tools (like Docker CLI or GitHub CLI), you can extend the base image. A sample extended Dockerfile is provided:

**Dockerfile.extended** - Extends the base image with Docker CLI and GitHub CLI

**Dockerfile.with-runbooks** - Packages a collection of verified runbooks into the container

**Dockerfile.extended-with-runbooks** - Combines both: tools (Docker CLI, GitHub CLI) and packaged runbooks

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

To package runbooks into a container:
```sh
# Create a runbooks directory with your verified runbooks
mkdir -p runbooks
cp my-runbook1.md my-runbook2.md runbooks/

# Build the image with runbooks
docker build -f Dockerfile.with-runbooks -t my-runbooks:latest .

# Execute a packaged runbook
docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -e GITHUB_TOKEN=$GITHUB_TOKEN \
    my-runbooks:latest \
    runbook execute --runbook /opt/stage0/runbooks/my-runbook1.md
```

You can combine approaches - extend the extended image and add runbooks:
```dockerfile
FROM ghcr.io/agile-learning-institute/stage0_runner:extended

# Copy your runbooks
RUN mkdir -p /opt/stage0/runbooks
COPY runbooks/ /opt/stage0/runbooks/
WORKDIR /opt/stage0/runbooks

# Add any additional tools if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends your-tool && \
    rm -rf /var/lib/apt/lists/*
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
├── Dockerfile                      # Base Docker configuration (minimal)
├── Dockerfile.extended             # Extended image with Docker CLI and GitHub CLI
├── Dockerfile.with-runbooks        # Image with packaged runbooks collection
├── Dockerfile.extended-with-runbooks # Combined: tools + runbooks
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
