#!/usr/bin/env python3
"""
Tests for the runbook service (merged RunbookRunner functionality).
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from services.runbook_service import RunbookService
from config.config import Config


def test_load_valid_runbook():
    """Test loading a valid runbook."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    content, name, errors, warnings = service._load_runbook(
        Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    )
    assert content is not None, "Should load valid runbook"
    assert name == "SimpleRunbook", "Should extract correct runbook name"
    assert len(errors) == 0, "Should have no errors"


def test_extract_sections():
    """Test extraction of runbook sections."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    content, name, errors, warnings = service._load_runbook(runbook_path)
    
    # Test section extraction
    doc_section = service._extract_section(content, 'Documentation')
    assert doc_section is not None, "Should extract Documentation section"
    
    script = service._extract_script(content)
    assert script is not None, "Should extract script"
    assert 'echo' in script, "Script should contain echo command"


def test_extract_env_vars():
    """Test extraction of environment variables from YAML."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    content, name, errors, warnings = service._load_runbook(runbook_path)
    
    env_section = service._extract_section(content, 'Environment Requirements')
    env_vars = service._extract_yaml_block(env_section)
    assert env_vars is not None, "Should extract env vars"
    assert 'TEST_VAR' in env_vars, "Should find TEST_VAR in env vars"


def test_extract_required_claims():
    """Test extraction of required claims from runbook."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    content, name, errors, warnings = service._load_runbook(runbook_path)
    
    required_claims = service._extract_required_claims(content)
    # SimpleRunbook should have required claims section
    assert required_claims is not None, "Should extract required claims"
    assert 'roles' in required_claims, "Should have roles claim"
    assert 'developer' in required_claims['roles'] or 'admin' in required_claims['roles'], "Should include developer or admin role"


def test_validate_runbook_content():
    """Test validation of runbook content."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    content, name, errors, warnings = service._load_runbook(runbook_path)
    
    # Set required environment variable
    os.environ['TEST_VAR'] = 'test_value'
    
    try:
        success, validation_errors, validation_warnings = service._validate_runbook_content(runbook_path, content)
        # Should pass validation if TEST_VAR is set
        assert success, f"Validation should pass. Errors: {validation_errors}"
    finally:
        # Clean up
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


def test_validate_missing_env_var():
    """Test validation fails when required env var is missing."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    content, name, errors, warnings = service._load_runbook(runbook_path)
    
    # Ensure TEST_VAR is not set
    if 'TEST_VAR' in os.environ:
        del os.environ['TEST_VAR']
    
    success, validation_errors, validation_warnings = service._validate_runbook_content(runbook_path, content)
    assert not success, "Validation should fail when env var is missing"
    assert any('TEST_VAR' in error for error in validation_errors), "Should report missing env var"


def test_script_timeout_enforcement():
    """Test that script execution times out after configured timeout."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    # Create a runbook content with a long-running script (sleep 10 seconds)
    # We'll set timeout to 2 seconds, so it should definitely timeout
    long_running_script = """#! /bin/zsh
sleep 10
echo "This should not appear"
"""
    
    runbook_content = f"""# TestRunbook
# Documentation
Test runbook for timeout
# Environment Requirements
```yaml
```
# File System Requirements
```yaml
Input:
Output:
```
# Script
```sh
{long_running_script}
```
# History
"""
    
    # Set a short timeout (2 seconds)
    config = Config.get_instance()
    original_timeout = config.SCRIPT_TIMEOUT_SECONDS
    original_max_output = config.MAX_OUTPUT_SIZE_BYTES
    
    try:
        config.SCRIPT_TIMEOUT_SECONDS = 2
        config.MAX_OUTPUT_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
        
        # Create a temporary runbook file
        test_runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'test_timeout_runbook.md'
        with open(test_runbook_path, 'w') as f:
            f.write(runbook_content)
        
        try:
            # Execute with short timeout
            return_code, stdout, stderr = service._execute_script(test_runbook_path, runbook_content)
            
            # Should timeout and return error
            assert return_code != 0, "Script should fail due to timeout"
            assert "timed out" in stderr.lower() or "timeout" in stderr.lower(), \
                f"Error message should mention timeout. Got: {stderr}"
            
        finally:
            # Clean up test file
            if test_runbook_path.exists():
                test_runbook_path.unlink()
    finally:
        # Restore original timeout
        config.SCRIPT_TIMEOUT_SECONDS = original_timeout
        config.MAX_OUTPUT_SIZE_BYTES = original_max_output


def test_output_size_limit():
    """Test that output is truncated when exceeding size limits."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    # Create a runbook that generates large output
    large_output_script = """#! /bin/zsh
# Generate 2MB of output
for i in {1..20000}; do
    echo "Line $i: This is a test line that repeats many times to exceed output limits"
done
"""
    
    runbook_content = f"""# TestRunbook
# Documentation
Test runbook for output limits
# Environment Requirements
```yaml
```
# File System Requirements
```yaml
Input:
Output:
```
# Script
```sh
{large_output_script}
```
# History
"""
    
    # Set a small output limit (100KB) and reasonable timeout
    config = Config.get_instance()
    original_max_output = config.MAX_OUTPUT_SIZE_BYTES
    original_timeout = config.SCRIPT_TIMEOUT_SECONDS
    
    try:
        config.MAX_OUTPUT_SIZE_BYTES = 100 * 1024  # 100KB
        config.SCRIPT_TIMEOUT_SECONDS = 60  # 60 seconds should be enough
        
        # Create a temporary runbook file
        test_runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'test_output_limit_runbook.md'
        with open(test_runbook_path, 'w') as f:
            f.write(runbook_content)
        
        try:
            # Execute script
            return_code, stdout, stderr = service._execute_script(test_runbook_path, runbook_content)
            
            # Output should be truncated
            stdout_size = len(stdout.encode('utf-8'))
            assert stdout_size <= config.MAX_OUTPUT_SIZE_BYTES, f"Stdout should be truncated to {config.MAX_OUTPUT_SIZE_BYTES} bytes, got {stdout_size}"
            
            # Should have warning about truncation
            if stdout_size >= config.MAX_OUTPUT_SIZE_BYTES:
                assert "truncated" in stderr.lower() or "warning" in stderr.lower(), "Should warn about truncation"
            
        finally:
            # Clean up test file
            if test_runbook_path.exists():
                test_runbook_path.unlink()
    finally:
        # Restore original values
        config.MAX_OUTPUT_SIZE_BYTES = original_max_output
        config.SCRIPT_TIMEOUT_SECONDS = original_timeout


def test_resource_monitoring_logging():
    """Test that resource usage is logged during script execution."""
    runbooks_dir = str(Path(__file__).parent.parent / 'samples' / 'runbooks')
    service = RunbookService(runbooks_dir)
    
    runbook_path = Path(__file__).parent.parent / 'samples' / 'runbooks' / 'SimpleRunbook.md'
    content, name, errors, warnings = service._load_runbook(runbook_path)
    
    # Set required environment variable
    os.environ['TEST_VAR'] = 'test_value'
    
    try:
        # Use patch to capture log messages
        import logging
        with patch('services.runbook_service.logger') as mock_logger:
            return_code, stdout, stderr = service._execute_script(runbook_path, content)
            
            # Verify that resource monitoring logs were called
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            # Should log execution start with resource limits
            assert any('timeout' in str(call).lower() or 'max_output' in str(call).lower() for call in info_calls), \
                "Should log resource limits before execution"
            
            # Should log execution completion with resource usage
            assert any('execution_time' in str(call).lower() or 'execution completed' in str(call).lower() for call in info_calls), \
                "Should log execution time and resource usage after completion"
                
    finally:
        # Clean up
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']


# Tests can be run with pytest or the custom runner below
if __name__ == '__main__':
    # Fallback: Simple test runner if pytest is not available
    import pytest
    pytest.main([__file__, '-v'])

