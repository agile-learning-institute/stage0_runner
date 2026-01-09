#!/usr/bin/env python3
"""
End-to-end (E2E) tests for stage0_runbook_api.

These are true black-box tests that assume the API server is already running
on the default port (8083). They make HTTP requests to test complete workflows
from API calls through runbook execution, including authentication, authorization,
error handling, and concurrent scenarios.

Tests use SimpleRunbook.md and restore it to original state after completion.

To run these tests:
1. Start the API server: pipenv run dev
2. In another terminal: pipenv run e2e
"""
import os
import json
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional

import pytest
import requests


# Path to SimpleRunbook.md
SIMPLE_RUNBOOK_PATH = Path(__file__).parent.parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
ORIGINAL_RUNBOOK_CONTENT: Optional[str] = None

# Default API base URL (assumes server is running on default port)
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8083')


def save_original_runbook():
    """Save the original content of SimpleRunbook.md."""
    global ORIGINAL_RUNBOOK_CONTENT
    if SIMPLE_RUNBOOK_PATH.exists():
        with open(SIMPLE_RUNBOOK_PATH, 'r', encoding='utf-8') as f:
            ORIGINAL_RUNBOOK_CONTENT = f.read()


def restore_original_runbook():
    """Restore SimpleRunbook.md to its original state using git."""
    global ORIGINAL_RUNBOOK_CONTENT
    # Use git to discard any changes (this is the primary method)
    try:
        subprocess.run(
            ['git', 'checkout', '--', str(SIMPLE_RUNBOOK_PATH)],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            check=False
        )
    except Exception:
        pass  # Git restore is best-effort
    
    # Fallback: restore from saved content if git didn't work
    if ORIGINAL_RUNBOOK_CONTENT is not None and SIMPLE_RUNBOOK_PATH.exists():
        try:
            with open(SIMPLE_RUNBOOK_PATH, 'w', encoding='utf-8') as f:
                f.write(ORIGINAL_RUNBOOK_CONTENT)
        except Exception:
            pass  # Best-effort restoration


@pytest.fixture(scope='session', autouse=True)
def setup_and_teardown():
    """Save original runbook before tests and restore after all tests."""
    save_original_runbook()
    yield
    restore_original_runbook()


@pytest.fixture(scope='session')
def api_base_url():
    """Get the API base URL (defaults to http://localhost:8083)."""
    return API_BASE_URL


@pytest.fixture(scope='session')
def check_server_running(api_base_url):
    """Check if the API server is running and accessible."""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f'{api_base_url}/metrics', timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_attempts - 1:
            time.sleep(0.5)
    
    pytest.skip(f"API server is not running at {api_base_url}. Please start the server first with 'pipenv run dev'")


@pytest.fixture
def dev_token(api_base_url, check_server_running):
    """Get a dev token with developer and admin roles."""
    response = requests.post(
        f'{api_base_url}/dev-login',
        json={'subject': 'e2e-test-user', 'roles': ['developer', 'admin']},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    data = response.json()
    return data['access_token']


@pytest.fixture
def viewer_token(api_base_url, check_server_running):
    """Get a dev token with viewer role only."""
    response = requests.post(
        f'{api_base_url}/dev-login',
        json={'subject': 'e2e-viewer-user', 'roles': ['viewer']},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    data = response.json()
    return data['access_token']


# ============================================================================
# E2E Test: Complete Runbook Workflow
# ============================================================================

def test_e2e_complete_runbook_workflow(api_base_url, check_server_running, dev_token):
    """Test complete workflow: list -> get -> validate -> execute -> check history."""
    # Step 1: List runbooks
    response = requests.get(
        f'{api_base_url}/api/runbooks',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'runbooks' in data
    assert any(rb['filename'] == 'SimpleRunbook.md' for rb in data['runbooks']), \
        "SimpleRunbook.md should be in the list"
    
    # Step 2: Get runbook content
    response = requests.get(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'content' in data
    assert 'SimpleRunbook' in data['name']
    assert 'TEST_VAR' in data['content'], "Runbook should contain TEST_VAR requirement"
    
    # Step 3: Get required environment variables
    response = requests.get(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/required-env',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'required' in data
    assert 'available' in data
    assert 'missing' in data
    assert any(env['name'] == 'TEST_VAR' for env in data['required'])
    
    # Step 4: Validate runbook (with env vars in request)
    response = requests.patch(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/validate',
        headers={'Authorization': f'Bearer {dev_token}'},
        json={'env_vars': {'TEST_VAR': 'e2e-test-value'}}
    )
    assert response.status_code in [200, 400]  # 200 if valid, 400 if invalid
    data = response.json()
    assert 'success' in data
    assert 'errors' in data
    assert 'warnings' in data
    
    # Step 5: Execute runbook
    response = requests.post(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/execute',
        headers={'Authorization': f'Bearer {dev_token}'},
        json={'env_vars': {'TEST_VAR': 'e2e-execution-test'}},
    )
    assert response.status_code in [200, 500]  # 200 if success, 500 if script fails
    data = response.json()
    assert 'success' in data
    assert 'return_code' in data
    assert 'stdout' in data
    assert 'stderr' in data
    assert 'runbook' in data
    assert data['runbook'] == 'SimpleRunbook.md'
    
    # Verify execution actually ran
    if data['success']:
        assert 'Running SimpleRunbook' in data['stdout'] or 'e2e-execution-test' in data['stdout']


# ============================================================================
# E2E Test: Authentication and Authorization Flows
# ============================================================================

def test_e2e_authentication_flow(api_base_url, check_server_running):
    """Test complete authentication flow: dev-login -> use token -> verify access."""
    # Step 1: Get token via dev-login
    response = requests.post(
        f'{api_base_url}/dev-login',
        json={'subject': 'auth-test-user', 'roles': ['developer']},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'
    token = data['access_token']
    
    # Step 2: Use token to access protected endpoint
    response = requests.get(
        f'{api_base_url}/api/runbooks',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    
    # Step 3: Verify token is required (unauthorized access)
    response = requests.get(f'{api_base_url}/api/runbooks')
    assert response.status_code == 401
    data = response.json()
    assert 'error' in data
    
    # Step 4: Verify invalid token is rejected
    response = requests.get(
        f'{api_base_url}/api/runbooks',
        headers={'Authorization': 'Bearer invalid-token-here'}
    )
    assert response.status_code == 401


def test_e2e_rbac_authorization_flow(api_base_url, check_server_running, dev_token, viewer_token):
    """Test RBAC authorization flow: viewer cannot execute runbook requiring admin."""
    # SimpleRunbook requires 'developer' or 'admin' role
    # viewer_token only has 'viewer' role
    
    # Step 1: Viewer can list runbooks (no RBAC required)
    response = requests.get(
        f'{api_base_url}/api/runbooks',
        headers={'Authorization': f'Bearer {viewer_token}'}
    )
    assert response.status_code == 200
    
    # Step 2: Viewer can get runbook content (no RBAC required)
    response = requests.get(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md',
        headers={'Authorization': f'Bearer {viewer_token}'}
    )
    assert response.status_code == 200
    
    # Step 3: Viewer cannot validate runbook (RBAC required)
    response = requests.patch(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/validate',
        headers={'Authorization': f'Bearer {viewer_token}'},
        json={'env_vars': {'TEST_VAR': 'test'}}
    )
    assert response.status_code == 403
    data = response.json()
    assert 'error' in data
    assert 'forbidden' in data['error'].lower() or 'rbac' in data['error'].lower() or 'claim' in data['error'].lower()
    
    # Step 4: Viewer cannot execute runbook (RBAC required)
    response = requests.post(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/execute',
        headers={'Authorization': f'Bearer {viewer_token}'},
        json={'env_vars': {'TEST_VAR': 'test'}},
    )
    assert response.status_code == 403
    data = response.json()
    assert 'error' in data
    
    # Step 5: Developer with proper role can execute
    response = requests.post(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/execute',
        headers={'Authorization': f'Bearer {dev_token}'},
        json={'env_vars': {'TEST_VAR': 'test'}},
    )
    assert response.status_code in [200, 500]  # May succeed or fail based on script


# ============================================================================
# E2E Test: Concurrent Execution Scenarios
# ============================================================================

def test_e2e_concurrent_list_requests(api_base_url, check_server_running, dev_token):
    """Test concurrent requests to list runbooks."""
    results = []
    errors = []
    
    def make_request(index):
        try:
            response = requests.get(
                f'{api_base_url}/api/runbooks',
                headers={'Authorization': f'Bearer {dev_token}'},
                timeout=10
            )
            results.append((index, response.status_code))
        except Exception as e:
            errors.append((index, str(e)))
    
    # Create 10 concurrent requests
    threads = []
    for i in range(10):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join(timeout=30)
    
    # Verify all requests succeeded
    assert len(errors) == 0, f"Concurrent requests failed: {errors}"
    assert len(results) == 10, f"Expected 10 results, got {len(results)}"
    assert all(status == 200 for _, status in results), \
        f"Not all requests succeeded: {results}"


def test_e2e_concurrent_executions(api_base_url, check_server_running, dev_token):
    """Test concurrent runbook executions."""
    results = []
    errors = []
    
    def execute_runbook(index):
        try:
            response = requests.post(
                f'{api_base_url}/api/runbooks/SimpleRunbook.md/execute',
                headers={'Authorization': f'Bearer {dev_token}'},
                json={'env_vars': {'TEST_VAR': f'concurrent-test-{index}'}},
                timeout=120
            )
            results.append((index, response.status_code))
        except Exception as e:
            errors.append((index, str(e)))
    
    # Create 5 concurrent executions
    threads = []
    for i in range(5):
        thread = threading.Thread(target=execute_runbook, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join(timeout=120)  # 2 minute timeout
    
    # All requests should complete
    assert len(errors) == 0, f"Concurrent executions failed: {errors}"
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    
    # All should return valid status codes
    status_codes = [status for _, status in results]
    assert all(status in [200, 500] for status in status_codes), \
        f"Unexpected status codes: {status_codes}"


# ============================================================================
# E2E Test: Error Response Formats
# ============================================================================

def test_e2e_error_response_format_401(api_base_url, check_server_running):
    """Test that 401 errors return proper format."""
    response = requests.get(f'{api_base_url}/api/runbooks')
    assert response.status_code == 401
    data = response.json()
    assert 'error' in data
    assert isinstance(data['error'], str)
    assert len(data['error']) > 0


def test_e2e_error_response_format_404(api_base_url, check_server_running, dev_token):
    """Test that 404 errors return proper format."""
    response = requests.get(
        f'{api_base_url}/api/runbooks/NonExistentRunbook.md',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 404
    data = response.json()
    assert 'error' in data
    assert isinstance(data['error'], str)
    assert 'not found' in data['error'].lower() or 'NonExistent' in data['error']


def test_e2e_error_response_format_403(api_base_url, check_server_running, viewer_token):
    """Test that 403 errors return proper format."""
    response = requests.post(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/execute',
        headers={'Authorization': f'Bearer {viewer_token}'},
        json={'env_vars': {'TEST_VAR': 'test'}},
    )
    assert response.status_code == 403
    data = response.json()
    assert 'error' in data
    assert isinstance(data['error'], str)


def test_e2e_error_response_format_400(api_base_url, check_server_running, dev_token):
    """Test that 400 errors return proper format (missing env var)."""
    # Try to validate without required env var (empty env_vars)
    response = requests.patch(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/validate',
        headers={'Authorization': f'Bearer {dev_token}'},
        json={'env_vars': {}}  # Send empty env_vars
    )
    # May return 200 with errors, or 400
    assert response.status_code in [200, 400]
    data = response.json()
    assert 'errors' in data or 'error' in data


# ============================================================================
# E2E Test: API Endpoints End-to-End
# ============================================================================

def test_e2e_all_endpoints_accessible(api_base_url, check_server_running, dev_token):
    """Test that all API endpoints are accessible and return expected formats."""
    # GET /api/runbooks
    response = requests.get(
        f'{api_base_url}/api/runbooks',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'success' in data
    assert 'runbooks' in data
    
    # GET /api/runbooks/<filename>
    response = requests.get(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'success' in data
    assert 'content' in data
    
    # GET /api/runbooks/<filename>/required-env
    response = requests.get(
        f'{api_base_url}/api/runbooks/SimpleRunbook.md/required-env',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'success' in data
    assert 'required' in data
    
    # GET /api/config
    response = requests.get(
        f'{api_base_url}/api/config',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'config_items' in data
    assert 'token' in data
    
    # GET /metrics (public endpoint)
    response = requests.get(f'{api_base_url}/metrics')
    assert response.status_code == 200
    
    # GET /docs/openapi.yaml (public endpoint)
    response = requests.get(f'{api_base_url}/docs/openapi.yaml')
    assert response.status_code == 200
    assert 'openapi' in response.text.lower()


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
