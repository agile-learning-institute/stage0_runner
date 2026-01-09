#!/usr/bin/env python3
"""
Unit tests for breadcrumb utilities.
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import uuid
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.flask_utils.breadcrumb import create_flask_breadcrumb


class TestCreateFlaskBreadcrumb:
    """Test create_flask_breadcrumb function."""
    
    def test_creates_breadcrumb_with_all_fields(self):
        """Test that breadcrumb contains all required fields."""
        token = {"user_id": "test_user"}
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"X-Correlation-Id": "test-correlation-id"}
        
        with patch('src.flask_utils.breadcrumb.request', mock_request):
            breadcrumb = create_flask_breadcrumb(token)
        
        assert "at_time" in breadcrumb
        assert "by_user" in breadcrumb
        assert "from_ip" in breadcrumb
        assert "correlation_id" in breadcrumb
        assert breadcrumb["by_user"] == "test_user"
        assert breadcrumb["from_ip"] == "192.168.1.1"
        assert breadcrumb["correlation_id"] == "test-correlation-id"
        assert isinstance(breadcrumb["at_time"], datetime)
    
    def test_creates_breadcrumb_without_correlation_id_header(self):
        """Test that breadcrumb generates UUID when correlation ID header is missing."""
        token = {"user_id": "test_user"}
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {}
        
        with patch('src.flask_utils.breadcrumb.request', mock_request):
            breadcrumb = create_flask_breadcrumb(token)
        
        assert "correlation_id" in breadcrumb
        # Should be a valid UUID string
        try:
            uuid.UUID(breadcrumb["correlation_id"])
        except ValueError:
            import pytest
            pytest.fail("correlation_id should be a valid UUID")
    
    def test_at_time_is_utc(self):
        """Test that at_time is in UTC timezone."""
        token = {"user_id": "test_user"}
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {}
        
        with patch('src.flask_utils.breadcrumb.request', mock_request):
            breadcrumb = create_flask_breadcrumb(token)
        
        assert breadcrumb["at_time"].tzinfo == timezone.utc

