#!/usr/bin/env python3
"""
Unit tests for route wrapper exception handling.
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Flask, jsonify
from src.flask_utils.route_wrapper import handle_route_exceptions
from src.flask_utils.exceptions import (
    HTTPUnauthorized,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError
)


class TestHandleRouteExceptions:
    """Test handle_route_exceptions decorator."""
    
    def test_successful_function_execution(self):
        """Test that successful function execution is not affected."""
        @handle_route_exceptions
        def test_function():
            return jsonify({"success": True}), 200
        
        app = Flask(__name__)
        with app.app_context():
            result, status = test_function()
            assert status == 200
            assert result.json == {"success": True}
    
    def test_http_unauthorized_exception(self):
        """Test that HTTPUnauthorized is handled correctly."""
        @handle_route_exceptions
        def test_function():
            raise HTTPUnauthorized("Invalid token")
        
        app = Flask(__name__)
        with app.app_context():
            result, status = test_function()
            assert status == 401
            assert result.json == {"error": "Invalid token"}
    
    def test_http_forbidden_exception(self):
        """Test that HTTPForbidden is handled correctly."""
        @handle_route_exceptions
        def test_function():
            raise HTTPForbidden("Insufficient permissions")
        
        app = Flask(__name__)
        with app.app_context():
            result, status = test_function()
            assert status == 403
            assert result.json == {"error": "Insufficient permissions"}
    
    def test_http_not_found_exception(self):
        """Test that HTTPNotFound is handled correctly."""
        @handle_route_exceptions
        def test_function():
            raise HTTPNotFound("Resource not found")
        
        app = Flask(__name__)
        with app.app_context():
            result, status = test_function()
            assert status == 404
            assert result.json == {"error": "Resource not found"}
    
    def test_http_internal_server_error_exception(self):
        """Test that HTTPInternalServerError is handled correctly."""
        @handle_route_exceptions
        def test_function():
            raise HTTPInternalServerError("Database error")
        
        app = Flask(__name__)
        with app.app_context():
            result, status = test_function()
            assert status == 500
            assert result.json == {"error": "Database error"}
    
    def test_rate_limit_exception(self):
        """Test that rate limit exception (429) is handled correctly."""
        class RateLimitExceeded(Exception):
            status_code = 429
        
        @handle_route_exceptions
        def test_function():
            raise RateLimitExceeded()
        
        app = Flask(__name__)
        with app.app_context():
            result, status = test_function()
            assert status == 429
            assert result.json == {"error": "Rate limit exceeded. Please try again later."}
    
    def test_unexpected_exception(self):
        """Test that unexpected exceptions are handled gracefully."""
        @handle_route_exceptions
        def test_function():
            raise ValueError("Unexpected error")
        
        app = Flask(__name__)
        with app.app_context():
            result, status = test_function()
            assert status == 500
            assert result.json == {"error": "A processing error occurred"}
    
    def test_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @handle_route_exceptions
        def test_function():
            """Test function docstring."""
            return jsonify({"success": True}), 200
        
        assert test_function.__name__ == "test_function"
        assert "Test function docstring" in test_function.__doc__

