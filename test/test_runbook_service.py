#!/usr/bin/env python3
"""
Tests for the runbook service (merged RunbookRunner functionality).
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from services.runbook_service import RunbookService


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


# Tests can be run with pytest or the custom runner below
if __name__ == '__main__':
    # Fallback: Simple test runner if pytest is not available
    import pytest
    pytest.main([__file__, '-v'])

