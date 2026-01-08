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

**Important Configuration Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `dev-secret-change-me` | **MUST be changed in production!** Secret for JWT signing/verification |
| `JWT_ISSUER` | `dev-idp` | Expected JWT issuer claim (must match identity provider) |
| `JWT_AUDIENCE` | `dev-api` | Expected JWT audience claim (must match identity provider) |
| `ENABLE_LOGIN` | `false` | Enable `/dev-login` endpoint (**NEVER enable in production**) |
| `API_PORT` | `8083` | Port number for the API server |
| `RUNBOOKS_DIR` | `./samples/runbooks` | Directory containing runbook files |
| `SCRIPT_TIMEOUT_SECONDS` | `600` | Maximum script execution time (10 minutes) |
| `MAX_OUTPUT_SIZE_BYTES` | `10485760` | Maximum script output size (10MB) |
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |
| `RATE_LIMIT_PER_MINUTE` | `60` | Requests per minute for most endpoints |
| `RATE_LIMIT_EXECUTE_PER_MINUTE` | `10` | Executions per minute (stricter limit) |
| `RATE_LIMIT_STORAGE_BACKEND` | `memory` | Rate limit storage: `memory` or `redis` |
| `REDIS_URL` | - | Required if `RATE_LIMIT_STORAGE_BACKEND=redis` |

**For complete configuration reference**, see [`src/config/config.py`](./src/config/config.py) which defines all configuration options, their types, defaults, and how they're loaded from environment variables.

**Example Configuration:**
```bash
export JWT_SECRET=$(openssl rand -hex 32)
export JWT_ISSUER="your-identity-provider"
export JWT_AUDIENCE="runbook-api-production"
export ENABLE_LOGIN="false"
export RATE_LIMIT_STORAGE_BACKEND="redis"
export REDIS_URL="redis://localhost:6379/0"
```

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

Runbooks can specify required claims in the "Required Claims" section to control access. See [RUNBOOK.md](./RUNBOOK.md#required-claims) for details on how to specify required claims and how RBAC validation works.

## Runbook Format

For complete details on runbook structure, required sections, history format, and execution processing, see [RUNBOOK.md](./RUNBOOK.md).

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

## Production Deployment Guide

This guide covers deploying the stage0_runbook_api to production environments.

### Prerequisites

- Docker and Docker Compose (or Kubernetes)
- Reverse proxy (nginx, Traefik, etc.) for TLS termination
- Identity provider configured for JWT token issuance
- Secret management system (for storing JWT secrets)
- Monitoring and logging infrastructure

### Deployment Options

#### Option 1: Docker Compose (Single Instance)

Best for: Small to medium deployments, single-server setups

**docker-compose.prod.yaml**:
```yaml
services:
  api:
    image: ghcr.io/agile-learning-institute/stage0_runbook_api:latest
    restart: always
    ports:
      - "127.0.0.1:8083:8083"  # Only expose to localhost, use reverse proxy
    environment:
      # Required Configuration
      API_PORT: 8083
      RUNBOOKS_DIR: /workspace/runbooks
      ENABLE_LOGIN: "false"  # MUST be false in production
      JWT_SECRET: "${JWT_SECRET}"  # From secrets manager
      JWT_ISSUER: "your-identity-provider"
      JWT_AUDIENCE: "runbook-api-production"
      
      # Recommended Configuration
      LOGGING_LEVEL: "WARNING"
      SCRIPT_TIMEOUT_SECONDS: "600"
      MAX_OUTPUT_SIZE_BYTES: "10485760"
      RATE_LIMIT_ENABLED: "true"
      RATE_LIMIT_PER_MINUTE: "60"
      RATE_LIMIT_EXECUTE_PER_MINUTE: "10"
      RATE_LIMIT_STORAGE_BACKEND: "memory"  # Use "redis" for multi-instance
      
      # Optional: Redis for distributed rate limiting
      # REDIS_URL: "redis://redis:6379/0"
    volumes:
      - ./runbooks:/workspace/runbooks:ro  # Read-only mount
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8083/metrics"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Redis for distributed rate limiting
  # redis:
  #   image: redis:7-alpine
  #   restart: always
  #   volumes:
  #     - redis-data:/data
  #   command: redis-server --appendonly yes

# volumes:
#   redis-data:
```

**Deployment Steps**:
1. Create runbooks directory: `mkdir -p runbooks`
2. Copy runbooks to the directory
3. Set environment variables (use secrets manager):
   ```bash
   export JWT_SECRET=$(openssl rand -hex 32)
   export JWT_ISSUER="your-idp"
   export JWT_AUDIENCE="runbook-api"
   ```
4. Start services: `docker-compose -f docker-compose.prod.yaml up -d`
5. Verify health: `curl http://localhost:8083/metrics`

#### Option 2: Docker Compose with Load Balancer (Multi-Instance)

Best for: High availability, horizontal scaling

**docker-compose.prod.yaml**:
```yaml
services:
  api:
    image: ghcr.io/agile-learning-institute/stage0_runbook_api:latest
    restart: always
    deploy:
      replicas: 3  # Run 3 instances
      resources:
        limits:
          cpus: '2'
          memory: 2G
    environment:
      API_PORT: 8083
      RUNBOOKS_DIR: /workspace/runbooks
      ENABLE_LOGIN: "false"
      JWT_SECRET: "${JWT_SECRET}"
      JWT_ISSUER: "your-identity-provider"
      JWT_AUDIENCE: "runbook-api-production"
      RATE_LIMIT_ENABLED: "true"
      RATE_LIMIT_STORAGE_BACKEND: "redis"  # Required for multi-instance
      REDIS_URL: "redis://redis:6379/0"
    volumes:
      - ./runbooks:/workspace/runbooks:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8083/metrics"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    deploy:
      resources:
        limits:
          memory: 512M

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # TLS certificates
    depends_on:
      - api

volumes:
  redis-data:
```

**nginx.conf** (reverse proxy configuration):
```nginx
upstream api_backend {
    least_conn;
    server api:8083 max_fails=3 fail_timeout=30s;
    # Add more instances if using multiple containers
}

server {
    listen 80;
    server_name runbook-api.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name runbook-api.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 600s;  # Match script timeout
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        allow 10.0.0.0/8;  # Internal network only
        deny all;
        proxy_pass http://api_backend;
    }
}
```

#### Option 3: Kubernetes Deployment

Best for: Cloud-native deployments, orchestrated environments

**k8s/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stage0-runbook-api
  namespace: runbooks
spec:
  replicas: 3
  selector:
    matchLabels:
      app: stage0-runbook-api
  template:
    metadata:
      labels:
        app: stage0-runbook-api
    spec:
      containers:
      - name: api
        image: ghcr.io/agile-learning-institute/stage0_runbook_api:latest
        ports:
        - containerPort: 8083
        env:
        - name: API_PORT
          value: "8083"
        - name: RUNBOOKS_DIR
          value: "/workspace/runbooks"
        - name: ENABLE_LOGIN
          value: "false"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: runbook-secrets
              key: jwt-secret
        - name: JWT_ISSUER
          value: "your-identity-provider"
        - name: JWT_AUDIENCE
          value: "runbook-api-production"
        - name: RATE_LIMIT_ENABLED
          value: "true"
        - name: RATE_LIMIT_STORAGE_BACKEND
          value: "redis"
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        volumeMounts:
        - name: runbooks
          mountPath: /workspace/runbooks
          readOnly: true
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /metrics
            port: 8083
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /metrics
            port: 8083
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: runbooks
        configMap:
          name: runbooks-config
---
apiVersion: v1
kind: Service
metadata:
  name: stage0-runbook-api
  namespace: runbooks
spec:
  selector:
    app: stage0-runbook-api
  ports:
  - port: 80
    targetPort: 8083
  type: ClusterIP
```

### Configuration Reference

#### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET` | Strong secret for JWT signing (MUST change from default) | `openssl rand -hex 32` |
| `JWT_ISSUER` | Expected JWT issuer claim | `your-identity-provider` |
| `JWT_AUDIENCE` | Expected JWT audience claim | `runbook-api-production` |
| `ENABLE_LOGIN` | MUST be `false` in production | `false` |

#### Recommended Configuration

| Variable | Default | Production Recommendation |
|----------|---------|---------------------------|
| `LOGGING_LEVEL` | `INFO` | `WARNING` or `ERROR` |
| `RATE_LIMIT_ENABLED` | `true` | `true` |
| `RATE_LIMIT_PER_MINUTE` | `60` | Adjust based on expected load |
| `RATE_LIMIT_EXECUTE_PER_MINUTE` | `10` | Adjust based on capacity |
| `RATE_LIMIT_STORAGE_BACKEND` | `memory` | `redis` for multi-instance |
| `SCRIPT_TIMEOUT_SECONDS` | `600` | Adjust based on runbook needs |
| `MAX_OUTPUT_SIZE_BYTES` | `10485760` | Adjust based on requirements |

#### Multi-Instance Configuration

For deployments with multiple API instances:
- **MUST** use `RATE_LIMIT_STORAGE_BACKEND=redis`
- **MUST** configure `REDIS_URL` pointing to a Redis instance
- **SHOULD** use shared storage for runbooks (read-only)
- **SHOULD** configure load balancer with health checks

### Monitoring Setup

#### Prometheus Metrics

The API exposes Prometheus metrics at `/metrics`. Configure Prometheus to scrape:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'stage0-runbook-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['api:8083']
    metrics_path: '/metrics'
    # Optional: Add authentication
    # bearer_token: 'your-token'
```

**Key Metrics to Monitor**:
- `flask_http_request_total` - Total HTTP requests by method, status, endpoint
- `flask_http_request_duration_seconds` - Request duration histogram
- `flask_exceptions_total` - Exception counts by type
- `gunicorn_workers` - Number of worker processes
- `gunicorn_requests_total` - Total requests processed

#### Grafana Dashboard

Create a Grafana dashboard with panels for:
- Request rate (requests/second)
- Error rate (4xx, 5xx responses)
- Response time (p50, p95, p99)
- Active workers
- Rate limit hits
- Script execution duration

#### Alerting Rules

**Prometheus Alert Rules** (`alerts.yml`):
```yaml
groups:
  - name: stage0_runbook_api
    rules:
      - alert: HighErrorRate
        expr: rate(flask_http_request_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, flask_http_request_duration_seconds_bucket) > 2
        for: 5m
        annotations:
          summary: "95th percentile response time > 2s"
          
      - alert: ServiceDown
        expr: up{job="stage0-runbook-api"} == 0
        for: 1m
        annotations:
          summary: "API service is down"
          
      - alert: HighRateLimitHits
        expr: rate(flask_http_request_total{status="429"}[5m]) > 10
        for: 5m
        annotations:
          summary: "High rate limit hits detected"
```

#### Log Aggregation

**Recommended Setup**:
- Use Docker logging driver or log forwarder (Fluentd, Fluent Bit)
- Send logs to centralized system (ELK, Loki, CloudWatch, etc.)
- Parse structured logs for:
  - Authentication failures
  - RBAC failures
  - Script execution failures
  - Rate limit hits

**Log Patterns to Monitor**:
- `RBAC failure` - Unauthorized access attempts
- `Script execution timed out` - Resource exhaustion
- `Invalid environment variable name` - Input validation failures
- `Rate limit exceeded` - DoS attempts

#### Health Checks

**Endpoint**: `GET /metrics` or `GET /api/runbooks`

**Health Check Script**:
```bash
#!/bin/bash
# healthcheck.sh
API_URL="${API_URL:-http://localhost:8083}"

# Check metrics endpoint
if curl -f -s "${API_URL}/metrics" > /dev/null; then
    echo "OK: Metrics endpoint healthy"
    exit 0
else
    echo "FAIL: Metrics endpoint unhealthy"
    exit 1
fi
```

### Load Balancing

When deploying multiple instances:

1. **Use a load balancer** (nginx, Traefik, AWS ALB, etc.)
2. **Configure health checks** to remove unhealthy instances
3. **Use session affinity** if needed (though API is stateless)
4. **Distribute rate limiting** using Redis backend
5. **Monitor per-instance metrics** to detect issues

### Backup and Recovery

**Runbooks**:
- Runbooks are stored in the `RUNBOOKS_DIR` directory
- **Backup regularly** using your standard backup procedures
- Consider version control (Git) for runbooks
- Test restore procedures

**History**:
- Execution history is stored in runbook files
- History is appended, so backups capture incremental changes
- Consider moving to database storage for high-volume deployments

### Performance Tuning

**Gunicorn Workers**:
- Default: 2 workers
- Recommended: `(2 × CPU cores) + 1`
- Adjust based on I/O vs CPU-bound workload

**Resource Limits**:
- Set appropriate CPU and memory limits
- Monitor actual usage and adjust
- Leave headroom for traffic spikes

**Rate Limiting**:
- Start with defaults (60 req/min, 10 exec/min)
- Monitor rate limit hits
- Adjust based on actual usage patterns

### Troubleshooting Production Issues

See the [Troubleshooting](#troubleshooting) section in SRE.md for common issues and solutions.

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
