"""
Runbook service for business logic and RBAC.

Handles RBAC checks and runbook operations (validate/execute).
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..command import RunbookRunner
from ..flask_utils.exceptions import HTTPNotFound, HTTPForbidden, HTTPInternalServerError
import logging

logger = logging.getLogger(__name__)


class RunbookService:
    """
    Service class for Runbook domain operations.
    
    Handles:
    - RBAC authorization checks based on required_claims in runbook
    - Runbook validation
    - Runbook execution
    - Business logic for Runbook domain
    """
    
    def __init__(self, runbooks_dir: str):
        """
        Initialize the RunbookService.
        
        Args:
            runbooks_dir: Path to directory containing runbooks
        """
        self.runbooks_dir = Path(runbooks_dir).resolve()
    
    def _resolve_runbook_path(self, filename: str) -> Path:
        """Get full path to a runbook file (with security check)."""
        # Security: prevent directory traversal
        safe_filename = os.path.basename(filename)
        return self.runbooks_dir / safe_filename
    
    def _check_rbac(self, token: Dict, required_claims: Optional[Dict[str, List[str]]], operation: str) -> bool:
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
    
    def validate_runbook(self, filename: str, token: Dict, breadcrumb: Dict) -> Dict:
        """
        Validate a runbook.
        
        Args:
            filename: The runbook filename
            token: Token dictionary with user_id and claims
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: Validation result with success, errors, and warnings
            
        Raises:
            HTTPNotFound: If runbook is not found
            HTTPForbidden: If RBAC check fails
        """
        runbook_path = self._resolve_runbook_path(filename)
        
        if not runbook_path.exists():
            raise HTTPNotFound(f"Runbook not found: {filename}")
        
        try:
            runner = RunbookRunner(str(runbook_path))
            
            # Load runbook to get required claims
            if not runner.load_runbook():
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract required claims and check RBAC
            required_claims = runner.extract_required_claims()
            self._check_rbac(token, required_claims, 'validate')
            
            # Perform validation
            success = runner.validate()
            
            return {
                "success": success,
                "runbook": filename,
                "errors": runner.errors,
                "warnings": runner.warnings
            }
            
        except HTTPForbidden as e:
            # Log RBAC failure to runbook history
            try:
                runner = RunbookRunner(str(runbook_path))
                if runner.load_runbook():
                    runner.append_rbac_failure_history(str(e), token.get('user_id', 'unknown'), 'validate')
            except Exception as log_error:
                logger.error(f"Failed to log RBAC failure to history: {log_error}")
            raise
        
        except Exception as e:
            logger.error(f"Error validating runbook {filename}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to validate runbook: {str(e)}")
    
    def execute_runbook(self, filename: str, token: Dict, breadcrumb: Dict, env_vars: Optional[Dict[str, str]] = None) -> Dict:
        """
        Execute a runbook.
        
        Args:
            filename: The runbook filename
            token: Token dictionary with user_id and claims
            breadcrumb: Breadcrumb dictionary for logging
            env_vars: Optional dictionary of environment variables to set
            
        Returns:
            dict: Execution result with success, return_code, stdout, stderr, etc.
            
        Raises:
            HTTPNotFound: If runbook is not found
            HTTPForbidden: If RBAC check fails
        """
        runbook_path = self._resolve_runbook_path(filename)
        
        if not runbook_path.exists():
            raise HTTPNotFound(f"Runbook not found: {filename}")
        
        # Set environment variables from env_vars dict
        original_env = {}
        if env_vars:
            for key, value in env_vars.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value
        
        try:
            runner = RunbookRunner(str(runbook_path))
            
            # Load runbook to get required claims
            if not runner.load_runbook():
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract required claims and check RBAC
            required_claims = runner.extract_required_claims()
            self._check_rbac(token, required_claims, 'execute')
            
            # Execute the runbook
            return_code = runner.execute()
            
            # Reload runbook to get updated content with history
            runner.load_runbook()
            
            # Extract the last execution history from the updated runbook content
            stdout_content = ""
            stderr_content = ""
            if runner.runbook_content:
                # Match the last history entry with stdout and stderr in code blocks
                history_pattern = r'## (\d{4}-\d{2}-\d{2}t[\d:\.]+).*?Return Code: (\d+).*?### stdout\s*```\s*\n(.*?)```.*?### stderr\s*```\s*\n(.*?)```'
                matches = list(re.finditer(history_pattern, runner.runbook_content, re.DOTALL))
                if matches:
                    last_match = matches[-1]
                    stdout_content = last_match.group(3).strip()
                    stderr_content = last_match.group(4).strip()
            
            return {
                "success": return_code == 0,
                "runbook": filename,
                "return_code": return_code,
                "stdout": stdout_content,
                "stderr": stderr_content,
                "errors": [],
                "warnings": []
            }
            
        except HTTPForbidden as e:
            # Log RBAC failure to runbook history
            try:
                runner = RunbookRunner(str(runbook_path))
                if runner.load_runbook():
                    runner.append_rbac_failure_history(str(e), token.get('user_id', 'unknown'), 'execute')
            except Exception as log_error:
                logger.error(f"Failed to log RBAC failure to history: {log_error}")
            raise
        
        except Exception as e:
            logger.error(f"Error executing runbook {filename}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to execute runbook: {str(e)}")
        
        finally:
            # Restore original environment variables
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    
    def list_runbooks(self, token: Dict, breadcrumb: Dict) -> Dict:
        """
        List all available runbooks.
        
        Args:
            token: Token dictionary with user_id and claims
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: List of runbooks with metadata
        """
        if not self.runbooks_dir.exists():
            raise HTTPNotFound(f"Runbooks directory not found: {self.runbooks_dir}")
        
        runbooks = []
        for file_path in self.runbooks_dir.glob('*.md'):
            try:
                runner = RunbookRunner(str(file_path))
                if runner.load_runbook():
                    runbooks.append({
                        "filename": file_path.name,
                        "name": runner.runbook_name,
                        "path": str(file_path.relative_to(self.runbooks_dir))
                    })
            except Exception:
                # Skip files that can't be loaded as runbooks
                continue
        
        return {
            "success": True,
            "runbooks": sorted(runbooks, key=lambda x: x['filename'])
        }
    
    def get_runbook(self, filename: str, token: Dict, breadcrumb: Dict) -> Dict:
        """
        Get runbook content.
        
        Args:
            filename: The runbook filename
            token: Token dictionary with user_id and claims
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: Runbook content and metadata
            
        Raises:
            HTTPNotFound: If runbook is not found
        """
        runbook_path = self._resolve_runbook_path(filename)
        
        if not runbook_path.exists():
            raise HTTPNotFound(f"Runbook not found: {filename}")
        
        try:
            with open(runbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            runner = RunbookRunner(str(runbook_path))
            runner.load_runbook()
            
            return {
                "success": True,
                "filename": filename,
                "name": runner.runbook_name,
                "content": content
            }
        except Exception as e:
            logger.error(f"Error reading runbook {filename}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to read runbook: {str(e)}")
    
    def get_required_env(self, filename: str, token: Dict, breadcrumb: Dict) -> Dict:
        """
        Get required environment variables for a runbook.
        
        Args:
            filename: The runbook filename
            token: Token dictionary with user_id and claims
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: Required, available, and missing environment variables
            
        Raises:
            HTTPNotFound: If runbook is not found
        """
        runbook_path = self._resolve_runbook_path(filename)
        
        if not runbook_path.exists():
            raise HTTPNotFound(f"Runbook not found: {filename}")
        
        try:
            runner = RunbookRunner(str(runbook_path))
            if not runner.load_runbook():
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract environment requirements
            env_section = runner.extract_section('Environment Requirements')
            if not env_section:
                return {
                    "success": True,
                    "filename": filename,
                    "required": [],
                    "available": [],
                    "missing": []
                }
            
            env_vars = runner.extract_yaml_block(env_section)
            if env_vars is None:
                return {
                    "success": True,
                    "filename": filename,
                    "required": [],
                    "available": [],
                    "missing": []
                }
            
            # Check which variables are set in the environment
            required = []
            available = []
            missing = []
            
            for var_name, description in env_vars.items():
                var_info = {
                    "name": var_name,
                    "description": description
                }
                required.append(var_info)
                
                if var_name in os.environ and os.environ[var_name]:
                    available.append(var_info)
                else:
                    missing.append(var_info)
            
            return {
                "success": True,
                "filename": filename,
                "required": required,
                "available": available,
                "missing": missing
            }
            
        except HTTPInternalServerError:
            raise
        except Exception as e:
            logger.error(f"Error getting required env for runbook {filename}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to get required environment variables: {str(e)}")

