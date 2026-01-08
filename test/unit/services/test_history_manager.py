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
    
    def test_append_history_creates_minified_json(self):
        """Test that append_history creates minified JSON."""
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
                "stdout", "stderr", token, breadcrumb, config_items
            )
            
            # Read file and verify JSON was appended
            with open(temp_path, 'r') as f:
                content = f.read()
            
            # Should have JSON line
            lines = content.strip().split('\n')
            json_line = [line for line in lines if line.startswith('{')]
            assert len(json_line) == 1
            
            # Parse JSON
            history = json.loads(json_line[0])
            assert history['return_code'] == 0
            assert history['operation'] == 'execute'
            assert history['stdout'] == 'stdout'
            assert history['stderr'] == 'stderr'
            assert history['breadcrumb']['roles'] == ['admin']
        finally:
            os.unlink(temp_path)
    
    def test_append_rbac_failure_history(self):
        """Test that append_rbac_failure_history creates RBAC failure entry."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = Path(f.name)
            f.write("# Test Runbook\n\n# History\n")
        
        try:
            token = {"user_id": "test_user", "roles": ["viewer"]}
            breadcrumb = {"at_time": datetime.now(timezone.utc), "correlation_id": "test-123"}
            config_items = []
            
            HistoryManager.append_rbac_failure_history(
                temp_path, "Access denied", "test_user", 'execute',
                token, breadcrumb, config_items
            )
            
            # Read file and verify JSON was appended
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            json_line = [line for line in lines if line.startswith('{')]
            assert len(json_line) == 1
            
            history = json.loads(json_line[0])
            assert history['return_code'] == 403
            assert 'RBAC Failure' in history['errors'][0]
        finally:
            os.unlink(temp_path)

