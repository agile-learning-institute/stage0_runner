#!/usr/bin/env python3
"""
Unit tests for RBACAuthorizer (focusing on edge cases).
"""
import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.rbac_authorizer import RBACAuthorizer
from src.flask_utils.exceptions import HTTPForbidden


class TestRBACAuthorizer:
    """Test RBACAuthorizer static methods."""
    
    def test_check_rbac_no_required_claims_allows(self):
        """Test that no required claims allows access."""
        token = {"claims": {}}
        result = RBACAuthorizer.check_rbac(token, None, 'execute')
        assert result is True
        
        result = RBACAuthorizer.check_rbac(token, {}, 'execute')
        assert result is True
    
    def test_check_rbac_token_claims_nested(self):
        """Test that check_rbac uses token['claims'] correctly."""
        token = {
            "user_id": "test_user",
            "claims": {
                "roles": ["admin"]
            }
        }
        required_claims = {"roles": ["admin", "developer"]}
        result = RBACAuthorizer.check_rbac(token, required_claims, 'execute')
        assert result is True
    
    def test_check_rbac_token_value_as_list(self):
        """Test that token value as list is handled correctly."""
        token = {
            "claims": {
                "roles": ["admin", "developer"]
            }
        }
        required_claims = {"roles": ["admin"]}
        result = RBACAuthorizer.check_rbac(token, required_claims, 'execute')
        assert result is True
    
    def test_check_rbac_token_value_as_string(self):
        """Test that token value as string is converted to list."""
        token = {
            "claims": {
                "roles": "admin"
            }
        }
        required_claims = {"roles": ["admin", "developer"]}
        result = RBACAuthorizer.check_rbac(token, required_claims, 'execute')
        assert result is True
    
    def test_check_rbac_token_value_non_string_non_list(self):
        """Test that non-string, non-list token value is converted."""
        token = {
            "claims": {
                "roles": 123  # Invalid type
            }
        }
        required_claims = {"roles": ["123"]}
        result = RBACAuthorizer.check_rbac(token, required_claims, 'execute')
        assert result is True
    
    def test_check_rbac_multiple_claims_all_required(self):
        """Test that multiple required claims all must match."""
        token = {
            "claims": {
                "roles": ["admin"],
                "department": "engineering"
            }
        }
        required_claims = {
            "roles": ["admin"],
            "department": ["engineering"]
        }
        result = RBACAuthorizer.check_rbac(token, required_claims, 'execute')
        assert result is True
    
    def test_check_rbac_missing_claim_raises_forbidden(self):
        """Test that missing claim raises HTTPForbidden."""
        token = {
            "claims": {
                "roles": ["viewer"]
            }
        }
        required_claims = {"roles": ["admin"]}
        with pytest.raises(HTTPForbidden):
            RBACAuthorizer.check_rbac(token, required_claims, 'execute')

