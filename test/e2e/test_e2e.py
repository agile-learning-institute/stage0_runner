#!/usr/bin/env python3
"""
End-to-end (E2E) tests for stage0_runbook_api.

These tests verify complete workflows from API calls through runbook execution,
including authentication, authorization, error handling, and concurrent scenarios.

Tests use SimpleRunbook.md and restore it to original state after completion.
"""
import os
import sys
import json
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pytest
from flask import Flask
from src.server import create_app
from src.config.config import Config


# Path to SimpleRunbook.md
SIMPLE_RUNBOOK_PATH = Path(__file__).parent.parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
ORIGINAL_RUNBOOK_CONTENT: Optional[str] = None


def save_original_runbook():
    """Save the original content of SimpleRunbook.md."""
    global ORIGINAL_RUNBOOK_CONTENT
    if SIMPLE_RUNBOOK_PATH.exists():
        with open(SIMPLE_RUNBOOK_PATH, 'r', encoding='utf-8') as f:
            ORIGINAL_RUNBOOK_CONTENT = f.read()


def restore_original_runbook():
    """Restore SimpleRunbook.md to its original state."""
    global ORIGINAL_RUNBOOK_CONTENT
    if ORIGINAL_RUNBOOK_CONTENT is not None and SIMPLE_RUNBOOK_PATH.exists():
        with open(SIMPLE_RUNBOOK_PATH, 'w', encoding='utf-8') as f:
            f.write(ORIGINAL_RUNBOOK_CONTENT)
        # Also use git to discard any changes
        try:
            subprocess.run(
                ['git', 'checkout', '--', str(SIMPLE_RUNBOOK_PATH)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                check=False
            )
        except Exception:
            pass  # Git restore is best-effort


@pytest.fixture(scope='session', autouse=True)
def setup_and_teardown():
    """Save original runbook before tests and restore after all tests."""
    save_original_runbook()
    yield
    restore_original_runbook()


@pytest.fixture
def flask_app():
    """Create Flask app for testing."""
    # Reset Config singleton to pick up new environment variables
    from src.config.config import Config
    Config._instance = None
    
    # Set test environment
    os.environ['ENABLE_LOGIN'] = 'true'
    os.environ['RUNBOOKS_DIR'] = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    os.environ['SCRIPT_TIMEOUT_SECONDS'] = '60'
    os.environ['MAX_OUTPUT_SIZE_BYTES'] = '10485760'
    os.environ['RATE_LIMIT_ENABLED'] = 'false'  # Disable rate limiting for e2e tests
    
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(flask_app):
    """Create Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def dev_token(client):
    """Get a dev token with developer and admin roles."""
    response = client.post(
        '/dev-login',
        json={'subject': 'e2e-test-user', 'roles': ['developer', 'admin']},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    return data['access_token']


@pytest.fixture
def viewer_token(client):
    """Get a dev token with viewer role only."""
    response = client.post(
        '/dev-login',
        json={'subject': 'e2e-viewer-user', 'roles': ['viewer']},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    return data['access_token']


# ============================================================================
# E2E Test: Complete Runbook Workflow
# ============================================================================

def test_e2e_complete_runbook_workflow(client, dev_token):
    """Test complete workflow: list -> get -> validate -> execute -> check history."""
    # Step 1: List runbooks
    response = client.get(
        '/api/runbooks',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'runbooks' in data
    assert any(rb['filename'] == 'SimpleRunbook.md' for rb in data['runbooks']), \
        "SimpleRunbook.md should be in the list"
    
    # Step 2: Get runbook content
    response = client.get(
        '/api/runbooks/SimpleRunbook.md',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'content' in data
    assert 'SimpleRunbook' in data['name']
    assert 'TEST_VAR' in data['content'], "Runbook should contain TEST_VAR requirement"
    
    # Step 3: Get required environment variables
    os.environ['TEST_VAR'] = 'e2e-test-value'
    try:
        response = client.get(
            '/api/runbooks/SimpleRunbook.md/required-env',
            headers={'Authorization': f'Bearer {dev_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'required' in data
        assert 'available' in data
        assert 'missing' in data
        assert any(env['name'] == 'TEST_VAR' for env in data['required'])
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']
    
    # Step 4: Validate runbook
    os.environ['TEST_VAR'] = 'e2e-test-value'
    try:
        response = client.patch(
            '/api/runbooks/SimpleRunbook.md/validate',
            headers={'Authorization': f'Bearer {dev_token}'},
            content_type='application/json'
        )
        assert response.status_code in [200, 400]  # 200 if valid, 400 if invalid
        data = json.loads(response.data)
        assert 'success' in data
        assert 'errors' in data
        assert 'warnings' in data
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']
    
    # Step 5: Execute runbook
    os.environ['TEST_VAR'] = 'e2e-execution-test'
    try:
        response = client.post(
            '/api/runbooks/SimpleRunbook.md/execute',
            headers={'Authorization': f'Bearer {dev_token}'},
            json={'env_vars': {'TEST_VAR': 'e2e-execution-test'}},
            content_type='application/json'
        )
        assert response.status_code in [200, 500]  # 200 if success, 500 if script fails
        data = json.loads(response.data)
        assert 'success' in data
        assert 'return_code' in data
        assert 'stdout' in data
        assert 'stderr' in data
        assert 'runbook' in data
        assert data['runbook'] == 'SimpleRunbook.md'
        
        # Verify execution actually ran
        if data['success']:
            assert 'Running SimpleRunbook' in data['stdout'] or 'e2e-execution-test' in data['stdout']
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


# ============================================================================
# E2E Test: Authentication and Authorization Flows
# ============================================================================

def test_e2e_authentication_flow(client):
    """Test complete authentication flow: dev-login -> use token -> verify access."""
    # Step 1: Get token via dev-login
    response = client.post(
        '/dev-login',
        json={'subject': 'auth-test-user', 'roles': ['developer']},
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'
    token = data['access_token']
    
    # Step 2: Use token to access protected endpoint
    response = client.get(
        '/api/runbooks',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Step 3: Verify token is required (unauthorized access)
    response = client.get('/api/runbooks')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    
    # Step 4: Verify invalid token is rejected
    response = client.get(
        '/api/runbooks',
        headers={'Authorization': 'Bearer invalid-token-here'}
    )
    assert response.status_code == 401


def test_e2e_rbac_authorization_flow(client, dev_token, viewer_token):
    """Test RBAC authorization flow: viewer cannot execute runbook requiring admin."""
    # SimpleRunbook requires 'developer' or 'admin' role
    # viewer_token only has 'viewer' role
    
    # Step 1: Viewer can list runbooks (no RBAC required)
    response = client.get(
        '/api/runbooks',
        headers={'Authorization': f'Bearer {viewer_token}'}
    )
    assert response.status_code == 200
    
    # Step 2: Viewer can get runbook content (no RBAC required)
    response = client.get(
        '/api/runbooks/SimpleRunbook.md',
        headers={'Authorization': f'Bearer {viewer_token}'}
    )
    assert response.status_code == 200
    
    # Step 3: Viewer cannot validate runbook (RBAC required)
    os.environ['TEST_VAR'] = 'test'
    try:
        response = client.patch(
            '/api/runbooks/SimpleRunbook.md/validate',
            headers={'Authorization': f'Bearer {viewer_token}'},
            content_type='application/json'
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert 'forbidden' in data['error'].lower() or 'rbac' in data['error'].lower() or 'claim' in data['error'].lower()
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']
    
    # Step 4: Viewer cannot execute runbook (RBAC required)
    os.environ['TEST_VAR'] = 'test'
    try:
        response = client.post(
            '/api/runbooks/SimpleRunbook.md/execute',
            headers={'Authorization': f'Bearer {viewer_token}'},
            json={'env_vars': {'TEST_VAR': 'test'}},
            content_type='application/json'
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']
    
    # Step 5: Developer with proper role can execute
    os.environ['TEST_VAR'] = 'test'
    try:
        response = client.post(
            '/api/runbooks/SimpleRunbook.md/execute',
            headers={'Authorization': f'Bearer {dev_token}'},
            json={'env_vars': {'TEST_VAR': 'test'}},
            content_type='application/json'
        )
        assert response.status_code in [200, 500]  # May succeed or fail based on script
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


# ============================================================================
# E2E Test: Concurrent Execution Scenarios
# ============================================================================

def test_e2e_concurrent_list_requests(client, dev_token):
    """Test concurrent requests to list runbooks."""
    results = []
    errors = []
    
    def make_request(index):
        try:
            response = client.get(
                '/api/runbooks',
                headers={'Authorization': f'Bearer {dev_token}'}
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


def test_e2e_concurrent_executions(client, dev_token):
    """Test concurrent runbook executions."""
    os.environ['TEST_VAR'] = 'concurrent-test'
    results = []
    errors = []
    
    def execute_runbook(index):
        try:
            response = client.post(
                '/api/runbooks/SimpleRunbook.md/execute',
                headers={'Authorization': f'Bearer {dev_token}'},
                json={'env_vars': {'TEST_VAR': f'concurrent-test-{index}'}},
                content_type='application/json'
            )
            results.append((index, response.status_code))
        except Exception as e:
            errors.append((index, str(e)))
    
    try:
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
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


# ============================================================================
# E2E Test: Error Response Formats
# ============================================================================

def test_e2e_error_response_format_401(client):
    """Test that 401 errors return proper format."""
    response = client.get('/api/runbooks')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert isinstance(data['error'], str)
    assert len(data['error']) > 0


def test_e2e_error_response_format_404(client, dev_token):
    """Test that 404 errors return proper format."""
    response = client.get(
        '/api/runbooks/NonExistentRunbook.md',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert isinstance(data['error'], str)
    assert 'not found' in data['error'].lower() or 'NonExistent' in data['error']


def test_e2e_error_response_format_403(client, viewer_token):
    """Test that 403 errors return proper format."""
    os.environ['TEST_VAR'] = 'test'
    try:
        response = client.post(
            '/api/runbooks/SimpleRunbook.md/execute',
            headers={'Authorization': f'Bearer {viewer_token}'},
            json={'env_vars': {'TEST_VAR': 'test'}},
            content_type='application/json'
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'error' in data
        assert isinstance(data['error'], str)
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


def test_e2e_error_response_format_400(client, dev_token):
    """Test that 400 errors return proper format (missing env var)."""
    # Try to validate without required env var
    if 'TEST_VAR' in os.environ:
        del os.environ['TEST_VAR']
    
    response = client.patch(
        '/api/runbooks/SimpleRunbook.md/validate',
        headers={'Authorization': f'Bearer {dev_token}'},
        content_type='application/json'
    )
    # May return 200 with errors, or 400
    assert response.status_code in [200, 400]
    data = json.loads(response.data)
    assert 'errors' in data or 'error' in data


# ============================================================================
# E2E Test: API Endpoints End-to-End
# ============================================================================

def test_e2e_all_endpoints_accessible(client, dev_token):
    """Test that all API endpoints are accessible and return expected formats."""
    # GET /api/runbooks
    response = client.get(
        '/api/runbooks',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'success' in data
    assert 'runbooks' in data
    
    # GET /api/runbooks/<filename>
    response = client.get(
        '/api/runbooks/SimpleRunbook.md',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'success' in data
    assert 'content' in data
    
    # GET /api/runbooks/<filename>/required-env
    os.environ['TEST_VAR'] = 'test'
    try:
        response = client.get(
            '/api/runbooks/SimpleRunbook.md/required-env',
            headers={'Authorization': f'Bearer {dev_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'success' in data
        assert 'required' in data
    finally:
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']
    
    # GET /api/config
    response = client.get(
        '/api/config',
        headers={'Authorization': f'Bearer {dev_token}'}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'config_items' in data
    assert 'token' in data
    
    # GET /metrics (public endpoint)
    response = client.get('/metrics')
    assert response.status_code == 200
    
    # GET /docs/openapi.yaml (public endpoint)
    response = client.get('/docs/openapi.yaml')
    assert response.status_code == 200
    assert 'openapi' in response.data.decode('utf-8').lower()


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

