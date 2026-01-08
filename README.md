# stage0_runbook_api

This repository contains the `stage0_runbook_api` - a production-ready REST API server for executing and validating runbooks. There is a WebUI `stage0_runbook_spa` available at [GitHub stage0_runbook_spa](https://github.com/agile-learning-institute/stage0_runbook_spa)

## Quick Start

A Runbook is a markdown file that describes an automated task. You can create a runbook for a manual task, but for an automated task it must have the proper [Runbook layout](./RUNBOOK.md). Here is an [empty template](./samples/runbooks/Runbook.md) runbook, and a [Simple Example](./samples/runbooks/SimpleRunbook.md) runbook.

### Using Makefile (Recommended for CLI)

```sh
# Validate a runbook using the API (via docker-compose)
RUNBOOK=SimpleRunbook.md ENV_VARS="TEST_VAR=test_value" make validate

# Execute a runbook using the API (via docker-compose)
RUNBOOK=SimpleRunbook.md ENV_VARS="TEST_VAR=test_value" make execute

# Start the API server for long-running use
make api
```

The Makefile automatically:
1. Starts the API server using docker-compose
2. Authenticates and gets a JWT token
3. Calls the appropriate API endpoint
4. Gracefully shuts down the API server

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

# Run tests
pipenv run test

# Start the API server (for development)
make api

# Build the deployment container
make container
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

The API server supports configuration via environment variables. The following configuration options are available:

### Server Configuration

- `API_PORT` (default: `8083`) - Port number for the API server
- `RUNBOOKS_DIR` (default: `./samples/runbooks`) - Directory containing runbook files
- `LOGGING_LEVEL` (default: `INFO`) - Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENABLE_LOGIN` (default: `false`) - Enable `/dev-login` endpoint for development

### Script Execution Resource Limits

- `SCRIPT_TIMEOUT_SECONDS` (default: `600`) - Maximum execution time for scripts in seconds (10 minutes). Scripts exceeding this timeout will be terminated.
- `MAX_OUTPUT_SIZE_BYTES` (default: `10485760`) - Maximum output size in bytes (10MB). Output exceeding this limit will be truncated with a warning.

**Example:**
```bash
export SCRIPT_TIMEOUT_SECONDS=300  # 5 minutes
export MAX_OUTPUT_SIZE_BYTES=5242880  # 5MB
```

### Rate Limiting

- `RATE_LIMIT_ENABLED` (default: `true`) - Enable/disable rate limiting on API endpoints
- `RATE_LIMIT_PER_MINUTE` (default: `60`) - Maximum requests per minute for most endpoints (GET, PATCH)
- `RATE_LIMIT_EXECUTE_PER_MINUTE` (default: `10`) - Maximum executions per minute for execute endpoint and dev-login (stricter limit)
- `RATE_LIMIT_STORAGE_BACKEND` (default: `memory`) - Storage backend for rate limiting: `memory` (single instance) or `redis` (distributed)

**Example:**
```bash
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_PER_MINUTE=100
export RATE_LIMIT_EXECUTE_PER_MINUTE=20
export RATE_LIMIT_STORAGE_BACKEND=redis  # For multi-instance deployments
export REDIS_URL=redis://localhost:6379/0  # Required if using redis backend
```

**Note:** When rate limits are exceeded, the API returns HTTP 429 (Too Many Requests) with an error message. Rate limit information is included in response headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`) when rate limiting is enabled.

### JWT Configuration

- `JWT_SECRET` (default: `dev-secret-change-me`) - Secret key for JWT signing/verification. **Must be changed in production!**
- `JWT_ALGORITHM` (default: `HS256`) - JWT signing algorithm
- `JWT_ISSUER` (default: `dev-idp`) - Expected JWT issuer claim
- `JWT_AUDIENCE` (default: `dev-api`) - Expected JWT audience claim
- `JWT_TTL_MINUTES` (default: `480`) - JWT token time-to-live in minutes (8 hours)

### Docker Compose Configuration

When using `docker-compose.cli.yaml`, environment variables can be set in the `environment` section:

```yaml
environment:
  API_PORT: 8083
  RUNBOOKS_DIR: /workspace/runbooks
  ENABLE_LOGIN: "true"
  SCRIPT_TIMEOUT_SECONDS: "600"
  MAX_OUTPUT_SIZE_BYTES: "10485760"
  LOGGING_LEVEL: "INFO"
```

## Authentication and Authorization

### Development Mode

When `ENABLE_LOGIN=true`, use the `/dev-login` endpoint to obtain JWT tokens:

```bash
curl -X POST http://localhost:8083/dev-login \
  -H "Content-Type: application/json" \
  -d '{"subject":"dev-user","roles":["developer","admin"]}'
```

**Never enable this in production!**

### Production Authentication

Configure your identity provider to issue JWTs with:
- `iss` (issuer) matching `JWT_ISSUER` config
- `aud` (audience) matching `JWT_AUDIENCE` config
- `roles` claim with user roles

### Role-Based Access Control (RBAC)

Runbooks can specify required claims in the "Required Claims" section:

```yaml
# Required Claims
roles: developer, admin, devops
```

When executing or validating a runbook:
1. The API extracts required claims from the runbook
2. Validates that the user's token contains the required claims
3. If validation fails, returns 403 Forbidden and logs the attempt to runbook history
4. If validation succeeds, proceeds with operation

## History Format

Execution history is stored as minified JSON (single line, no whitespace) in the runbook's History section. Each execution or validation operation appends a history entry to the runbook file and logs the same value. The history document is described [here](./docs/history-schema.json).

## Execution Processing

1. Validate runbook structure and requirements (fail-fast)
2. Check RBAC permissions based on required claims
3. Create temp.zsh with the contents of the script
4. Set executable permissions on temp.zsh (`chmod +x`)
5. Invoke temp.zsh and capture stdout and stderr
6. Append execution history as minified JSON to runbook
7. Log execution history to application logs
8. Remove temp.zsh

## Security

### Security Features

The API implements several security measures to protect against common vulnerabilities:

#### Authentication and Authorization
- **JWT-based authentication** - All API endpoints (except `/dev-login`, `/metrics`, and `/docs`) require valid JWT tokens
- **Role-Based Access Control (RBAC)** - Runbooks can specify required claims that users must have to execute or validate
- **Token validation** - JWT tokens are validated for signature, expiration, issuer, and audience
- **Dev-login protection** - The `/dev-login` endpoint is disabled by default and must be explicitly enabled

#### Input Validation and Sanitization
- **Environment variable validation** - Environment variable names are validated (alphanumeric + underscore only)
- **Environment variable sanitization** - Control characters are removed from environment variable values (newlines/tabs preserved for scripts)
- **Path traversal protection** - Runbook filenames are sanitized to prevent directory traversal attacks
- **YAML parsing** - Uses PyYAML's `safe_load()` to prevent code execution vulnerabilities

#### Resource Limits
- **Script timeout** - Scripts are terminated after a configurable timeout (default: 10 minutes)
- **Output size limits** - Script output is truncated to prevent memory exhaustion (default: 10MB)
- **Rate limiting** - API endpoints are rate-limited to prevent DoS attacks (default: 60 req/min, 10 exec/min)

#### Execution Isolation
- **Temporary directory isolation** - Scripts are executed in isolated temporary directories per execution
- **Automatic cleanup** - Temporary directories and files are cleaned up after execution, even on errors

### Production Security Requirements

**CRITICAL: The following must be configured before deploying to production:**

1. **JWT Configuration**
   - **MUST** change `JWT_SECRET` from default `dev-secret-change-me` to a strong, randomly generated secret
   - **MUST** configure `JWT_ISSUER` and `JWT_AUDIENCE` to match your identity provider
   - **MUST** use a secure token TTL appropriate for your security policy

2. **Disable Development Features**
   - **MUST** set `ENABLE_LOGIN=false` (or omit it, as false is default) to disable `/dev-login` endpoint
   - **NEVER** enable dev-login in production - it allows anyone to generate tokens with arbitrary roles

3. **Rate Limiting**
   - **SHOULD** enable rate limiting (`RATE_LIMIT_ENABLED=true`)
   - **SHOULD** configure appropriate limits for your expected load
   - **SHOULD** use Redis backend (`RATE_LIMIT_STORAGE_BACKEND=redis`) for multi-instance deployments

4. **Network Security**
   - **MUST** use HTTPS/TLS in production (configure via reverse proxy or load balancer)
   - **SHOULD** restrict network access to the API server
   - **SHOULD** use a reverse proxy (nginx, Traefik, etc.) for additional security layers

5. **Container Security**
   - **SHOULD** run containers as non-root user
   - **SHOULD** use read-only file systems where possible
   - **SHOULD** limit container capabilities
   - **SHOULD** scan container images for vulnerabilities

6. **Monitoring and Logging**
   - **SHOULD** monitor for failed authentication attempts
   - **SHOULD** log all runbook executions and RBAC failures
   - **SHOULD** set up alerts for suspicious activity
   - **SHOULD** monitor resource usage (CPU, memory, disk)

### Known Limitations and Security Considerations

#### Script Execution Security

**IMPORTANT:** Scripts executed by runbooks run with the same privileges as the API server process. This means:

- Scripts have **full access to the file system** within the container/host
- Scripts can **access the network** if network access is available
- Scripts can **modify system state** (files, environment variables, etc.)
- Scripts can **access other processes** running on the same system

**Recommendations:**
- **Only execute trusted runbooks** - Review runbook scripts before execution
- **Use container isolation** - Consider executing runbooks in isolated Docker containers (see SRE.md)
- **Run as non-root** - Ensure the API server runs with minimal privileges
- **Network isolation** - Consider network policies to restrict script network access
- **File system restrictions** - Use read-only mounts where possible

#### Concurrent Execution

- **File race conditions** - Concurrent executions of the same runbook may result in history entries being interleaved or lost. This is a known limitation when using file-based history storage.
- **Resource contention** - Multiple concurrent script executions may compete for system resources (CPU, memory, disk I/O)

**Recommendations:**
- **Limit concurrency** - Use rate limiting to control concurrent executions
- **Monitor resource usage** - Set up alerts for high resource consumption
- **Consider database storage** - For high-concurrency scenarios, consider moving history to a database

#### Development Mode Security

When `ENABLE_LOGIN=true`:
- The `/dev-login` endpoint allows **anyone** to generate tokens with **arbitrary roles**
- CORS is set to allow all origins (`Access-Control-Allow-Origin: *`)
- JWT signature verification may be bypassed if using default `JWT_SECRET`

**NEVER enable development mode in production!**

#### Threat Model

The API is designed to protect against:
- ✅ Unauthorized access (via JWT authentication)
- ✅ Path traversal attacks (via filename sanitization)
- ✅ Resource exhaustion (via timeouts and output limits)
- ✅ DoS attacks (via rate limiting)
- ✅ Command injection via environment variables (via validation/sanitization)

The API does **NOT** protect against:
- ❌ Malicious scripts in trusted runbooks (scripts run with full privileges)
- ❌ Insider threats (users with valid tokens can execute any runbook they have access to)
- ❌ Network-based attacks on script execution (scripts can make network calls)
- ❌ File system attacks from within scripts (scripts have file system access)

### Security Best Practices

1. **Principle of Least Privilege**
   - Grant users only the minimum roles/claims needed
   - Use RBAC to restrict access to sensitive runbooks
   - Run the API server with minimal system privileges

2. **Defense in Depth**
   - Use multiple security layers (network, application, container)
   - Implement monitoring and alerting
   - Regular security audits and updates

3. **Secure Configuration**
   - Use strong, randomly generated secrets
   - Store secrets in secure secret management systems
   - Rotate secrets regularly

4. **Runbook Review**
   - Review all runbook scripts before execution
   - Use version control for runbooks
   - Implement runbook approval workflows for sensitive operations

5. **Monitoring and Incident Response**
   - Monitor authentication failures
   - Log all runbook executions
   - Set up alerts for suspicious activity
   - Have an incident response plan

### Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
- **DO NOT** open a public GitHub issue
- Contact the maintainers directly
- Provide detailed information about the vulnerability
- Allow time for the issue to be addressed before public disclosure

## SRE Guidance

See [SRE.md](../stage0_runbooks/SRE.md) in the stage0_runbooks repository for detailed technical guidance on:
- Extending base images with additional tools
- Packaging runbooks into containers
- Production configuration
- Monitoring and metrics
- Troubleshooting

## Project Structure

```
.
├── Dockerfile                      # Base Docker configuration
├── docker-compose.cli.yaml        # Docker Compose for CLI operations
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
│   │   ├── breadcrumb.py          # Request breadcrumbs
│   │   └── ejson_encoder.py       # JSON encoder
│   ├── routes/                    # API route blueprints
│   │   ├── config_routes.py
│   │   ├── dev_login_routes.py
│   │   ├── explorer_routes.py
│   │   ├── metric_routes.py
│   │   ├── runbook_routes.py
│   │   └── shutdown_routes.py
│   ├── services/                  # Business logic layer
│   │   └── runbook_service.py     # Runbook operations (merged RunbookRunner)
│   └── server.py                  # Flask application factory
└── test/
    └── test_runbook_service.py    # Unit tests for the service
```
