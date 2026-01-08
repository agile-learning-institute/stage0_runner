#!/usr/bin/env python3
"""
Unit tests for Token class and utilities.
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import jwt
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.flask_utils.token import Token, create_flask_token
from src.flask_utils.exceptions import HTTPUnauthorized
from src.config.config import Config


class TestTokenInitialization:
    """Test Token class initialization."""
    
    def setup_method(self):
        """Reset config before each test."""
        Config._instance = None
        os.environ['JWT_SECRET'] = 'dev-secret-change-me'
        os.environ['JWT_ALGORITHM'] = 'HS256'
        os.environ['JWT_ISSUER'] = 'dev-idp'
        os.environ['JWT_AUDIENCE'] = 'dev-api'
    
    def teardown_method(self):
        """Clean up environment variables."""
        for key in ['JWT_SECRET', 'JWT_ALGORITHM', 'JWT_ISSUER', 'JWT_AUDIENCE']:
            if key in os.environ:
                del os.environ[key]
    
    def test_missing_authorization_header(self):
        """Test that missing Authorization header raises HTTPUnauthorized."""
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {}
        
        with patch('src.flask_utils.token.request', mock_request):
            with pytest.raises(HTTPUnauthorized, match="Missing or invalid Authorization header"):
                Token(mock_request)
    
    def test_invalid_authorization_header_format(self):
        """Test that invalid Authorization header format raises HTTPUnauthorized."""
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": "InvalidFormat token"}
        
        with patch('src.flask_utils.token.request', mock_request):
            with pytest.raises(HTTPUnauthorized, match="Missing or invalid Authorization header"):
                Token(mock_request)
    
    def test_empty_token(self):
        """Test that empty token raises HTTPUnauthorized."""
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": "Bearer "}
        
        with patch('src.flask_utils.token.request', mock_request):
            with pytest.raises(HTTPUnauthorized, match="Empty token in Authorization header"):
                Token(mock_request)
    
    def test_valid_token_development_mode(self):
        """Test that valid token in development mode is decoded."""
        # Create a test token
        payload = {
            'sub': 'test_user',
            'roles': ['admin'],
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            token = Token(mock_request)
        
        assert token.claims['sub'] == 'test_user'
        assert token.remote_ip == "192.168.1.1"
    
    def test_expired_token(self):
        """Test that expired token raises HTTPUnauthorized."""
        # Create an expired token
        payload = {
            'sub': 'test_user',
            'exp': int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            with pytest.raises(HTTPUnauthorized, match="Token has expired"):
                Token(mock_request)


class TestTokenClaimMapping:
    """Test token claim mapping."""
    
    def setup_method(self):
        """Reset config before each test."""
        Config._instance = None
        os.environ['JWT_SECRET'] = 'dev-secret-change-me'
    
    def teardown_method(self):
        """Clean up environment variables."""
        if 'JWT_SECRET' in os.environ:
            del os.environ['JWT_SECRET']
    
    def test_sub_maps_to_user_id(self):
        """Test that 'sub' claim is mapped to 'user_id'."""
        payload = {
            'sub': 'test_user',
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            token = Token(mock_request)
        
        assert token.claims['user_id'] == 'test_user'
        assert token.claims['sub'] == 'test_user'
    
    def test_roles_string_converted_to_list(self):
        """Test that roles string is converted to list."""
        payload = {
            'sub': 'test_user',
            'roles': 'admin,developer',
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            token = Token(mock_request)
        
        assert token.claims['roles'] == ['admin', 'developer']
    
    def test_roles_list_preserved(self):
        """Test that roles list is preserved."""
        payload = {
            'sub': 'test_user',
            'roles': ['admin', 'developer'],
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            token = Token(mock_request)
        
        assert token.claims['roles'] == ['admin', 'developer']
    
    def test_missing_roles_defaults_to_empty_list(self):
        """Test that missing roles defaults to empty list."""
        payload = {
            'sub': 'test_user',
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            token = Token(mock_request)
        
        assert token.claims['roles'] == []


class TestTokenToDict:
    """Test token to_dict method."""
    
    def setup_method(self):
        """Reset config before each test."""
        Config._instance = None
        os.environ['JWT_SECRET'] = 'dev-secret-change-me'
    
    def teardown_method(self):
        """Clean up environment variables."""
        if 'JWT_SECRET' in os.environ:
            del os.environ['JWT_SECRET']
    
    def test_to_dict_contains_all_fields(self):
        """Test that to_dict contains all expected fields."""
        payload = {
            'sub': 'test_user',
            'roles': ['admin'],
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            token = Token(mock_request)
            token_dict = token.to_dict()
        
        assert 'user_id' in token_dict
        assert 'roles' in token_dict
        assert 'remote_ip' in token_dict
        assert 'claims' in token_dict
        assert token_dict['user_id'] == 'test_user'
        assert token_dict['roles'] == ['admin']
        assert token_dict['remote_ip'] == "192.168.1.1"


class TestCreateFlaskToken:
    """Test create_flask_token function."""
    
    def setup_method(self):
        """Reset config before each test."""
        Config._instance = None
        os.environ['JWT_SECRET'] = 'dev-secret-change-me'
    
    def teardown_method(self):
        """Clean up environment variables."""
        if 'JWT_SECRET' in os.environ:
            del os.environ['JWT_SECRET']
    
    def test_create_flask_token_returns_dict(self):
        """Test that create_flask_token returns a dictionary."""
        payload = {
            'sub': 'test_user',
            'roles': ['admin'],
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }
        token_string = jwt.encode(payload, 'dev-secret', algorithm='HS256')
        
        mock_request = Mock()
        mock_request.remote_addr = "192.168.1.1"
        mock_request.headers = {"Authorization": f"Bearer {token_string}"}
        
        with patch('src.flask_utils.token.request', mock_request):
            token_dict = create_flask_token()
        
        assert isinstance(token_dict, dict)
        assert 'user_id' in token_dict
        assert 'roles' in token_dict
        assert token_dict['user_id'] == 'test_user'

