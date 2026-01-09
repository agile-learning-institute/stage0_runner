#!/usr/bin/env python3
"""
Unit tests for custom HTTP exceptions.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.flask_utils.exceptions import (
    HTTPUnauthorized,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError
)


class TestHTTPUnauthorized:
    """Test HTTPUnauthorized exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        exc = HTTPUnauthorized()
        assert exc.status_code == 401
        assert exc.message == "Unauthorized"
        assert str(exc) == "Unauthorized"
    
    def test_custom_message(self):
        """Test exception with custom message."""
        exc = HTTPUnauthorized("Custom unauthorized message")
        assert exc.status_code == 401
        assert exc.message == "Custom unauthorized message"
        assert str(exc) == "Custom unauthorized message"


class TestHTTPForbidden:
    """Test HTTPForbidden exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        exc = HTTPForbidden()
        assert exc.status_code == 403
        assert exc.message == "Forbidden"
        assert str(exc) == "Forbidden"
    
    def test_custom_message(self):
        """Test exception with custom message."""
        exc = HTTPForbidden("Custom forbidden message")
        assert exc.status_code == 403
        assert exc.message == "Custom forbidden message"
        assert str(exc) == "Custom forbidden message"


class TestHTTPNotFound:
    """Test HTTPNotFound exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        exc = HTTPNotFound()
        assert exc.status_code == 404
        assert exc.message == "Not Found"
        assert str(exc) == "Not Found"
    
    def test_custom_message(self):
        """Test exception with custom message."""
        exc = HTTPNotFound("Resource not found: /api/test")
        assert exc.status_code == 404
        assert exc.message == "Resource not found: /api/test"
        assert str(exc) == "Resource not found: /api/test"


class TestHTTPInternalServerError:
    """Test HTTPInternalServerError exception."""
    
    def test_default_message(self):
        """Test exception with default message."""
        exc = HTTPInternalServerError()
        assert exc.status_code == 500
        assert exc.message == "Internal Server Error"
        assert str(exc) == "Internal Server Error"
    
    def test_custom_message(self):
        """Test exception with custom message."""
        exc = HTTPInternalServerError("Database connection failed")
        assert exc.status_code == 500
        assert exc.message == "Database connection failed"
        assert str(exc) == "Database connection failed"

