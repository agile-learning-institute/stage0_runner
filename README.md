# stage0_runbook_api

This repository contains the `stage0_runbook_api` component of the [Stage0 Runbook System](https://github.com/agile-learning-institute/stage0_runbooks) - a production-ready REST API server for validating and executing runbooks. There is a WebUI `stage0_runbook_spa` available at [GitHub stage0_runbook_spa](https://github.com/agile-learning-institute/stage0_runbook_spa)

## Quick Start

A Runbook is just a markdown file that describes an automated task. You can create a runbook for a manual task, but for an automated task it must have the proper [Runbook layout](./RUNBOOK.md). See the [Custom Runbook Template](https://github.com/agile-learning-institute/stage0_runbook_api/blob/harden_for_prod/samples/runbooks/Runbook.md) for instructions on setting up your own runbook system.

### Using Makefile (Recommended for Testing)

The Makefile provides simple curl-based commands for testing runbooks without requiring Python or the CLI tool:

```sh
# Start API in dev mode with local runbooks mounted
make dev

# Validate a runbook (API must be running)
make validate RUNBOOK=samples/runbooks/SimpleRunbook.md

# Execute a runbook with environment variables
make execute RUNBOOK=samples/runbooks/SimpleRunbook.md ENV='TEST_VAR=test_value'

# Start the packaged API server for long-running use
make api

# Build the container and package runbooks
make container

# Open web UI in browser
make open

# Stop all services
make down
```

The Makefile uses `curl` to interact with the API:
- Automatically gets a dev token from `/dev-login`
- Calls the appropriate API endpoint
- Formats JSON output using `jq`

**Prerequisites**: `make`, `curl`, and `jq` (for JSON formatting)

### Using the API Directly

All operations require JWT authentication. For development, use the `/dev-login` endpoint to get a token:

```sh
# Get a token
TOKEN=$(curl -s -X POST http://localhost:8083/dev-login \
  -H "Content-Type: application/json" \
  -d '{"subject":"dev-user","roles":["developer","admin"]}' | \
  jq -r '.access_token')

# Validate a runbook
curl -X PATCH "http://localhost:8083/api/runbooks/SimpleRunbook.md" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Execute a runbook with environment variables
curl -X POST "http://localhost:8083/api/runbooks/SimpleRunbook.md" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"env_vars":{"TEST_VAR":"test_value"}}'

# List all runbooks
curl -X GET "http://localhost:8083/api/runbooks" \
  -H "Authorization: Bearer $TOKEN"

# Get runbook content
curl -X GET "http://localhost:8083/api/runbooks/SimpleRunbook.md" \
  -H "Authorization: Bearer $TOKEN"

# Shutdown the API server
curl -X POST "http://localhost:8083/api/shutdown" \
  -H "Authorization: Bearer $TOKEN"
```

## Contributing Prerequisites

- Python 3.12+
- pipenv (install with `pip install pipenv`)
- Docker and Docker Compose (for container-based execution)

## Developer Commands

```sh
# Install dependencies
pipenv install

# Run unit and integration tests (uses Flask test client, no running API required)
pipenv run test

# Run end-to-end (e2e) tests (comprehensive workflow tests)
pipenv run e2e

# Run the API server locally (development mode)
pipenv run dev

# Start the API server in a container (uses container built by 'make container')
make api

# Build the deployment container
make container

# All together now
make container && make api && pipenv run e2e
```

## API Server

The API server runs via Gunicorn and provides:
- REST API endpoints for runbook operations (with JWT authentication)
- Prometheus metrics endpoint at `/metrics`
- API Explorer UI at `/docs/explorer.html` for interactive API documentation
- Dev login endpoint at `/dev-login` (when `ENABLE_LOGIN=true`)
- Config endpoint at `/api/config`
- Shutdown endpoint at `/api/shutdown` (for graceful shutdown)

### API Endpoints

- `GET /api/runbooks` - List all available runbooks
- `GET /api/runbooks/<filename>` - Get runbook content
- `GET /api/runbooks/<filename>/required-env` - Get required environment variables
- `PATCH /api/runbooks/<filename>/validate` - Validate a runbook
- `POST /api/runbooks/<filename>/execute` - Execute a runbook
- `POST /api/shutdown` - Gracefully shutdown the server
- `GET /api/config` - Get configuration (with JWT)
- `POST /dev-login` - Get JWT token for development (if enabled)
- `GET /metrics` - Prometheus metrics
- `GET /docs/<path>` - API Explorer and documentation

All endpoints except `/dev-login`, `/metrics`, and `/docs` require JWT authentication.

### API Explorer

The API Explorer is available at `/docs/explorer.html` and provides:
- Interactive API documentation using Swagger UI
- Try-it-out functionality for testing endpoints
- Full OpenAPI specification rendering
- Example requests and responses

The OpenAPI specification is available at `/docs/openapi.yaml`.

**Access the explorer:**
```
http://localhost:8083/docs/explorer.html
http://localhost:8083/docs/openapi.yaml
```

## Configuration

The API server uses a centralized `Config` singleton (see [`src/config/config.py`](./src/config/config.py)) that manages all configuration via environment variables with sensible defaults.

**Key Configuration Variables:**
- `API_PORT` - Port for the API server (default: `8083`)
- `RUNBOOKS_DIR` - Directory containing runbooks (default: `./samples/runbooks`)
- `ENABLE_LOGIN` - Enable `/dev-login` endpoint for development (default: `false`, **NEVER enable in production**)
- `JWT_SECRET` - Secret for JWT signing (**MUST be changed in production**)
- `JWT_ISSUER` - Expected JWT issuer claim
- `JWT_AUDIENCE` - Expected JWT audience claim

**For complete configuration reference**, see [`src/config/config.py`](./src/config/config.py) which defines all configuration options, their types, defaults, and how they're loaded from environment variables.

**For production configuration guidance**, including required settings, recommended values, and deployment examples, see the [SRE Documentation](https://github.com/agile-learning-institute/stage0_runbooks/blob/main/SRE.md#production-configuration).

## Authentication and Authorization

### Development Mode

When `ENABLE_LOGIN=true`, use the `/dev-login` endpoint to obtain JWT tokens:

```bash
curl -X POST http://localhost:8083/dev-login \
  -H "Content-Type: application/json" \
  -d '{"subject":"dev-user","roles":["developer","admin"]}'
```

**Never enable this in production!**

### Production Authentication and RBAC

For production authentication setup, JWT configuration, and Role-Based Access Control (RBAC) details, see the [SRE Documentation](https://github.com/agile-learning-institute/stage0_runbooks/blob/main/SRE.md#authentication-and-authorization).

Runbooks can specify required claims in the "Required Claims" section to control access. See [RUNBOOK.md](./RUNBOOK.md#required-claims) for details on how to specify required claims and how RBAC validation works.

## Runbook Format

For complete details on runbook structure, required sections, history format, and execution processing, see [RUNBOOK.md](./RUNBOOK.md).

## Security

For comprehensive security documentation, including security features, production requirements, known limitations, threat model, and best practices, see [SECURITY.md](./SECURITY.md).


## Production Deployment Guide

For comprehensive production deployment documentation, including deployment options (Docker Compose single/multi-instance, Kubernetes), configuration reference, monitoring setup, load balancing, backup/recovery, and performance tuning, see [SRE.md](https://github.com/agile-learning-institute/stage0_runbooks/blob/main/SRE.md) in the stage0_runbooks repository.

## Project Structure

```
.
├── Dockerfile                      # Base Docker configuration
├── docker-compose.yaml            # Docker Compose configuration
├── samples/                       # Sample Dockerfiles and example runbooks
│   ├── Dockerfile.extended        # Extended image with Docker CLI and GitHub CLI
│   ├── Dockerfile.with-runbooks   # Image with packaged runbooks collection
│   ├── Dockerfile.extended-with-runbooks # Combined: tools + runbooks
│   └── runbooks/                  # Example runbooks
│       ├── SimpleRunbook.md
│       ├── CreatePackage.md
│       └── CreatePackage.dockerfile
├── Makefile                       # Make targets for container operations
├── Pipfile                        # Python dependencies (pipenv)
├── README.md                      # This file
├── RUNBOOK.md                     # Runbook format specification
├── docs/
│   ├── explorer.html              # API Explorer (Swagger UI)
│   ├── history-schema.json        # JSON schema for history entries
│   └── openapi.yaml               # OpenAPI specification
├── src/
│   ├── config/                    # Configuration management
│   │   └── config.py
│   ├── flask_utils/               # Flask utilities
│   │   ├── token.py               # JWT token handling
│   │   ├── exceptions.py          # HTTP exceptions
│   │   ├── route_wrapper.py       # Exception handling decorator
│   │   └── breadcrumb.py          # Request breadcrumbs
│   ├── routes/                    # API route blueprints
│   │   ├── config_routes.py
│   │   ├── dev_login_routes.py
│   │   ├── explorer_routes.py
│   │   ├── metric_routes.py
│   │   ├── runbook_routes.py
│   │   └── shutdown_routes.py
│   ├── services/                  # Business logic layer
│   │   ├── runbook_service.py     # Runbook service (orchestrator)
│   │   ├── runbook_parser.py      # Markdown parsing
│   │   ├── runbook_validator.py   # Runbook validation
│   │   ├── script_executor.py     # Script execution
│   │   ├── history_manager.py     # History management
│   │   └── rbac_authorizer.py     # RBAC authorization
│   └── server.py                  # Flask application factory
└── test/
    └── test_runbook_service.py    # Unit tests for the service
```
