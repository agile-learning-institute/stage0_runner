#!/usr/bin/env python3
"""
Runbook CLI - Command-line interface for interacting with the Runbook API.

This CLI wraps the REST API and provides convenient commands for:
- Validating runbooks
- Executing runbooks
- Listing runbooks
- Getting runbook content
- Getting required environment variables
"""
import argparse
import json
import os
import sys
import time
from typing import Dict, Optional
import urllib.request
import urllib.error


class RunbookCLI:
    """CLI client for the Runbook API."""
    
    def __init__(self, api_url: str = "http://localhost:8083", timeout: int = 30):
        """
        Initialize the CLI client.
        
        Args:
            api_url: Base URL of the API server
            timeout: Timeout in seconds for waiting for API to be healthy
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.token: Optional[str] = None
    
    def wait_for_api(self) -> bool:
        """
        Wait for the API to be healthy.
        
        Returns:
            True if API is healthy, False otherwise
        """
        metrics_url = f"{self.api_url}/metrics"
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                req = urllib.request.Request(metrics_url)
                with urllib.request.urlopen(req, timeout=2) as response:
                    if response.getcode() == 200:
                        return True
            except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                pass
            
            time.sleep(1)
        
        return False
    
    def get_token(self, subject: str = "cli-user", roles: list = None) -> Optional[str]:
        """
        Get a JWT token from the dev-login endpoint.
        
        Args:
            subject: Subject for the token
            roles: List of roles for the token
        
        Returns:
            JWT token string, or None if failed
        """
        if roles is None:
            roles = ["developer", "admin"]
        
        dev_login_url = f"{self.api_url}/dev-login"
        data = json.dumps({"subject": subject, "roles": roles}).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                dev_login_url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    self.token = result.get('access_token')
                    return self.token
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"ERROR: Failed to get authentication token: {e}", file=sys.stderr)
            return None
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> tuple[Optional[Dict], int]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PATCH)
            endpoint: API endpoint path
            data: Optional request body data
            headers: Optional additional headers
        
        Returns:
            Tuple of (response_data, status_code)
        """
        url = f"{self.api_url}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        headers.setdefault("Content-Type", "application/json")
        
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
        
        try:
            req = urllib.request.Request(url, data=request_data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=600) as response:
                status_code = response.getcode()
                body = response.read().decode('utf-8')
                try:
                    result = json.loads(body) if body else {}
                    return result, status_code
                except json.JSONDecodeError:
                    return {"error": body}, status_code
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            try:
                error_data = json.loads(body) if body else {}
                return error_data, e.code
            except json.JSONDecodeError:
                return {"error": body}, e.code
        except urllib.error.URLError as e:
            return {"error": str(e)}, 0
    
    def list_runbooks(self) -> int:
        """List all available runbooks."""
        result, status_code = self._make_request("GET", "/api/runbooks")
        
        if status_code == 200:
            print(json.dumps(result, indent=2))
            return 0
        else:
            print(f"ERROR: Failed to list runbooks (HTTP {status_code})", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            return 1
    
    def get_runbook(self, filename: str) -> int:
        """Get runbook content."""
        result, status_code = self._make_request("GET", f"/api/runbooks/{filename}")
        
        if status_code == 200:
            print(json.dumps(result, indent=2))
            return 0
        else:
            print(f"ERROR: Failed to get runbook (HTTP {status_code})", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            return 1
    
    def get_required_env(self, filename: str) -> int:
        """Get required environment variables for a runbook."""
        result, status_code = self._make_request("GET", f"/api/runbooks/{filename}/required-env")
        
        if status_code == 200:
            print(json.dumps(result, indent=2))
            return 0
        else:
            print(f"ERROR: Failed to get required environment variables (HTTP {status_code})", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            return 1
    
    def validate_runbook(self, filename: str) -> int:
        """Validate a runbook."""
        result, status_code = self._make_request("PATCH", f"/api/runbooks/{filename}/validate")
        
        success = result.get('success', False) if result else False
        print(json.dumps(result, indent=2))
        
        if status_code == 200 and success:
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            for warning in warnings:
                print(f"WARNING: {warning}", file=sys.stderr)
            return 0 if success else 1
        else:
            print(f"ERROR: Validation failed (HTTP {status_code})", file=sys.stderr)
            return 1
    
    def execute_runbook(self, filename: str, env_vars: Optional[Dict[str, str]] = None) -> int:
        """Execute a runbook."""
        data = {}
        if env_vars:
            data["env_vars"] = env_vars
        
        result, status_code = self._make_request(
            "POST",
            f"/api/runbooks/{filename}/execute",
            data=data if data else None
        )
        
        success = result.get('success', False) if result else False
        return_code = result.get('return_code', 1) if result else 1
        
        print(json.dumps(result, indent=2))
        
        if status_code == 200 and success and return_code == 0:
            return 0
        else:
            print(f"ERROR: Execution failed (HTTP {status_code}, return code: {return_code})", file=sys.stderr)
            return return_code if return_code != 0 else 1
    
    def shutdown(self) -> int:
        """Shutdown the API server."""
        result, status_code = self._make_request("POST", "/api/shutdown")
        
        if status_code == 200:
            print("API server shutdown successfully")
            return 0
        else:
            print(f"ERROR: Failed to shutdown API server (HTTP {status_code})", file=sys.stderr)
            return 1


def parse_env_vars(env_string: str) -> Dict[str, str]:
    """
    Parse environment variables from string format.
    
    Args:
        env_string: Space-separated KEY=VALUE pairs
    
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    if env_string:
        for pair in env_string.split():
            if '=' in pair:
                key, value = pair.split('=', 1)
                env_vars[key] = value
    return env_vars


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Runbook CLI - Command-line interface for the Runbook API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a runbook
  runbook validate SimpleRunbook.md

  # Execute a runbook with environment variables
  runbook execute SimpleRunbook.md --env-vars "TEST_VAR=test_value ANOTHER=value"

  # List all runbooks
  runbook list

  # Get runbook content
  runbook get SimpleRunbook.md

  # Get required environment variables
  runbook required-env SimpleRunbook.md
        """
    )
    
    parser.add_argument(
        '--api-url',
        default=os.getenv('API_URL', 'http://localhost:8083'),
        help='API server URL (default: http://localhost:8083 or API_URL env var)'
    )
    parser.add_argument(
        '--wait-timeout',
        type=int,
        default=30,
        help='Timeout in seconds for waiting for API to be healthy (default: 30)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Do not wait for API to be healthy'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute', required=True)
    
    # List command
    subparsers.add_parser('list', help='List all available runbooks')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get runbook content')
    get_parser.add_argument('filename', help='Runbook filename')
    
    # Required-env command
    req_env_parser = subparsers.add_parser('required-env', help='Get required environment variables')
    req_env_parser.add_argument('filename', help='Runbook filename')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a runbook')
    validate_parser.add_argument('filename', help='Runbook filename')
    
    # Execute command
    execute_parser = subparsers.add_parser('execute', help='Execute a runbook')
    execute_parser.add_argument('filename', help='Runbook filename')
    execute_parser.add_argument(
        '--env-vars',
        help='Environment variables as space-separated KEY=VALUE pairs'
    )
    
    # Shutdown command
    subparsers.add_parser('shutdown', help='Shutdown the API server')
    
    args = parser.parse_args()
    
    # Initialize CLI client
    cli = RunbookCLI(api_url=args.api_url, timeout=args.wait_timeout)
    
    # Wait for API if needed
    if not args.no_wait and args.command != 'shutdown':
        print("Waiting for API to be healthy...", file=sys.stderr)
        if not cli.wait_for_api():
            print(f"ERROR: API did not become healthy within {args.wait_timeout} seconds", file=sys.stderr)
            return 1
        print("API is healthy", file=sys.stderr)
    
    # Get authentication token
    if args.command != 'shutdown':
        print("Getting authentication token...", file=sys.stderr)
        if not cli.get_token():
            print("ERROR: Failed to get authentication token", file=sys.stderr)
            return 1
    
    # Execute command
    if args.command == 'list':
        return cli.list_runbooks()
    elif args.command == 'get':
        return cli.get_runbook(args.filename)
    elif args.command == 'required-env':
        return cli.get_required_env(args.filename)
    elif args.command == 'validate':
        return cli.validate_runbook(args.filename)
    elif args.command == 'execute':
        env_vars = parse_env_vars(args.env_vars) if args.env_vars else None
        return cli.execute_runbook(args.filename, env_vars)
    elif args.command == 'shutdown':
        return cli.shutdown()
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
