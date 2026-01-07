#!/usr/bin/env python3
"""
Tests for the stage0_runner command utility.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from command import RunbookRunner


def test_load_valid_runbook():
    """Test loading a valid runbook."""
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    runner = RunbookRunner(str(runbook_path))
    assert runner.load_runbook(), "Should load valid runbook"
    assert runner.runbook_name == "SimpleRunbook", "Should extract correct runbook name"
    assert runner.runbook_content is not None, "Should have runbook content"


def test_validate_simple_runbook():
    """Test validation of SimpleRunbook."""
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    runner = RunbookRunner(str(runbook_path))
    
    # Set required environment variable
    os.environ['TEST_VAR'] = 'test_value'
    
    try:
        result = runner.validate()
        # Should pass validation if TEST_VAR is set
        assert result, f"Validation should pass. Errors: {runner.errors}"
    finally:
        # Clean up
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


def test_validate_missing_env_var():
    """Test validation fails when required env var is missing."""
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    runner = RunbookRunner(str(runbook_path))
    
    # Ensure TEST_VAR is not set
    if 'TEST_VAR' in os.environ:
        del os.environ['TEST_VAR']
    
    result = runner.validate()
    assert not result, "Validation should fail when env var is missing"
    assert any('TEST_VAR' in error for error in runner.errors), "Should report missing env var"


def test_extract_sections():
    """Test extraction of runbook sections."""
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    runner = RunbookRunner(str(runbook_path))
    runner.load_runbook()
    
    # Test section extraction
    doc_section = runner.extract_section('Documentation')
    assert doc_section is not None, "Should extract Documentation section"
    
    script = runner.extract_script()
    assert script is not None, "Should extract script"
    assert 'echo' in script, "Script should contain echo command"


def test_extract_env_vars():
    """Test extraction of environment variables from YAML."""
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    runner = RunbookRunner(str(runbook_path))
    runner.load_runbook()
    
    env_section = runner.extract_section('Environment Requirements')
    env_vars = runner.extract_yaml_block(env_section)
    assert env_vars is not None, "Should extract env vars"
    assert 'TEST_VAR' in env_vars, "Should find TEST_VAR in env vars"


def test_execute_simple_runbook():
    """Test execution of SimpleRunbook."""
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    runner = RunbookRunner(str(runbook_path))
    
    # Set required environment variable
    os.environ['TEST_VAR'] = 'test_execution_value'
    
    try:
        return_code = runner.execute()
        assert return_code == 0, "Execution should succeed"
        
        # Verify history was appended
        with open(runbook_path, 'r') as f:
            content = f.read()
            assert '## 20' in content, "Should have history entry with timestamp"
            assert 'Return Code: 0' in content, "Should record return code"
            assert '### stdout' in content, "Should have stdout section"
            assert '### stderr' in content, "Should have stderr section"
    finally:
        # Clean up
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


def test_validate_create_package_runbook():
    """Test validation of CreatePackage runbook."""
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'CreatePackage.md'
    runner = RunbookRunner(str(runbook_path))
    
    # Set required environment variable
    os.environ['GITHUB_TOKEN'] = 'test_token'
    
    try:
        result = runner.validate()
        # Should pass if GITHUB_TOKEN is set and dockerfile exists
        if not result:
            print(f"Validation errors: {runner.errors}")
            print(f"Warnings: {runner.warnings}")
    finally:
        # Clean up
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']


if __name__ == '__main__':
    # Simple test runner
    tests = [
        test_load_valid_runbook,
        test_extract_sections,
        test_extract_env_vars,
        test_validate_simple_runbook,
        test_validate_missing_env_var,
        test_execute_simple_runbook,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"Running {test.__name__}...")
            test()
            print(f"  ✓ {test.__name__} passed")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\nTests: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)

