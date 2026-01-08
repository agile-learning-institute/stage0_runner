"""
RBAC authorizer for role-based access control checks.

Handles authorization checks based on required claims in runbooks.
"""
from typing import Dict, List, Optional
import logging

from ..flask_utils.exceptions import HTTPForbidden
from .runbook_parser import RunbookParser

logger = logging.getLogger(__name__)


class RBACAuthorizer:
    """
    Authorizer for role-based access control.
    
    Handles:
    - Extracting required claims from runbooks
    - Checking if tokens have required claims
    - Raising HTTPForbidden on authorization failures
    """
    
    @staticmethod
    def extract_required_claims(content: str) -> Optional[Dict[str, List[str]]]:
        """
        Extract required claims from runbook content.
        
        Args:
            content: Runbook content string
            
        Returns:
            Dictionary of required claims (claim_name -> list of allowed values), or None
        """
        return RunbookParser.extract_required_claims(content)
    
    @staticmethod
    def check_rbac(token: Dict, required_claims: Optional[Dict[str, List[str]]], operation: str) -> bool:
        """
        Check if the token has the required claims for the operation.
        
        Args:
            token: Token dictionary with claims
            required_claims: Dictionary of required claims (claim_name -> list of allowed values)
            operation: The operation being performed (e.g., 'validate', 'execute')
        
        Returns:
            bool: True if authorized, False otherwise
            
        Raises:
            HTTPForbidden: If RBAC check fails
        """
        # If no required claims are specified, allow access
        if not required_claims:
            return True
        
        token_claims = token.get('claims', {})
        missing_claims = []
        
        # Check each required claim
        for claim_name, allowed_values in required_claims.items():
            token_value = token_claims.get(claim_name)
            
            # If claim is not in token, authorization fails
            if token_value is None:
                missing_claims.append(f"{claim_name} (not present)")
                continue
            
            # Convert token value to list if it's a string
            if isinstance(token_value, str):
                token_value_list = [token_value]
            elif isinstance(token_value, list):
                token_value_list = token_value
            else:
                token_value_list = [str(token_value)]
            
            # Check if any of the token values match allowed values
            has_match = any(tv in allowed_values for tv in token_value_list)
            
            if not has_match:
                # Format the token value for error message
                token_display = ', '.join(token_value_list) if isinstance(token_value_list, list) else str(token_value)
                missing_claims.append(
                    f"{claim_name}={token_display} (required: {', '.join(allowed_values)})"
                )
        
        if missing_claims:
            error_message = f"RBAC check failed for {operation}. Missing or invalid claims: {', '.join(missing_claims)}"
            logger.warning(f"RBAC failure for user {token.get('user_id')}: {error_message}")
            raise HTTPForbidden(error_message)
        
        return True

