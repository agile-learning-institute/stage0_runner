#!/usr/bin/env python3
"""
Unit tests for HistoryManager.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.history_manager import HistoryManager


class TestHistoryManager:
    """Test HistoryManager static methods."""
    
    def test_append_history_creates_markdown(self):
        """Test that append_history creates human-readable markdown."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = Path(f.name)
            f.write("# Test Runbook\n\n# History\n")
        
        try:
            start_time = datetime.now(timezone.utc)
            finish_time = datetime.now(timezone.utc)
            token = {"user_id": "test_user", "roles": ["admin"]}
            breadcrumb = {"at_time": start_time, "correlation_id": "test-123"}
            config_items = [{"name": "TEST", "value": "value", "from": "default"}]
            
            HistoryManager.append_history(
                temp_path, start_time, finish_time, 0, 'execute',
                "stdout text", "stderr text", token, breadcrumb, config_items
            )
            
            # Read file and verify markdown was appended
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Should have markdown format with timestamp, exit code, stdout, stderr
            assert "###" in content, "Should have markdown heading (###)"
            assert "Exit Code: 0" in content, "Should show exit code"
            assert "**Stdout:**" in content, "Should have stdout section"
            assert "**Stderr:**" in content, "Should have stderr section"
            assert "stdout text" in content, "Should contain stdout content"
            assert "stderr text" in content, "Should contain stderr content"
            assert finish_time.strftime('%Y-%m-%dT%H:%M:%S') in content, "Should contain timestamp"
        finally:
            os.unlink(temp_path)
    
    def test_append_rbac_failure_history(self):
        """Test that append_rbac_failure_history creates RBAC failure entry in markdown."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = Path(f.name)
            f.write("# Test Runbook\n\n# History\n")
        
        try:
            token = {"user_id": "test_user", "roles": ["viewer"]}
            timestamp = datetime.now(timezone.utc)
            breadcrumb = {"at_time": timestamp, "correlation_id": "test-123"}
            config_items = []
            
            HistoryManager.append_rbac_failure_history(
                temp_path, "Access denied", "test_user", 'execute',
                token, breadcrumb, config_items
            )
            
            # Read file and verify markdown was appended
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Should have markdown format with timestamp, exit code 403, error message
            assert "###" in content, "Should have markdown heading (###)"
            assert "Exit Code: 403" in content, "Should show exit code 403"
            assert "**Error:**" in content, "Should have error section"
            assert "RBAC Failure" in content, "Should contain RBAC failure message"
            assert "test_user" in content, "Should contain user ID"
        finally:
            os.unlink(temp_path)

