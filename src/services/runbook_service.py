"""
Runbook service for business logic and orchestration.

Orchestrates runbook operations using specialized components:
- RunbookParser: Markdown parsing
- RunbookValidator: Validation logic
- ScriptExecutor: Script execution
- HistoryManager: History management
- RBACAuthorizer: Authorization checks
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..flask_utils.exceptions import HTTPNotFound, HTTPForbidden, HTTPInternalServerError
from ..config.config import Config
from .runbook_parser import RunbookParser
from .runbook_validator import RunbookValidator
from .script_executor import ScriptExecutor
from .history_manager import HistoryManager
from .rbac_authorizer import RBACAuthorizer
import logging

logger = logging.getLogger(__name__)


class RunbookService:
    """
    Service class for Runbook domain operations.
    
    Orchestrates runbook operations using specialized components:
    - RunbookParser: Extracts content from markdown files
    - RunbookValidator: Validates runbook structure and requirements
    - ScriptExecutor: Executes scripts with resource limits
    - HistoryManager: Manages execution history
    - RBACAuthorizer: Handles authorization checks
    
    Public API:
    - validate_runbook: Validate a runbook
    - execute_runbook: Execute a runbook
    - list_runbooks: List all available runbooks
    - get_runbook: Get runbook content
    - get_required_env: Get required environment variables
    """
    
    def __init__(self, runbooks_dir: str):
        """
        Initialize the RunbookService.
        
        Args:
            runbooks_dir: Path to directory containing runbooks
        """
        self.runbooks_dir = Path(runbooks_dir).resolve()
        self.config = Config.get_instance()
    
    def _resolve_runbook_path(self, filename: str) -> Path:
        """Get full path to a runbook file (with security check)."""
        # Security: prevent directory traversal
        safe_filename = os.path.basename(filename)
        return self.runbooks_dir / safe_filename
    
    def validate_runbook(self, filename: str, token: Dict, breadcrumb: Dict, env_vars: dict = None) -> Dict:
        """
        Validate a runbook.
        
        Args:
            filename: The runbook filename
            token: Token dictionary with user_id and claims
            breadcrumb: Breadcrumb dictionary for logging
            env_vars: Optional dict of environment variables to use for validation
            
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
            # Load runbook
            content, name, load_errors, load_warnings = RunbookParser.load_runbook(runbook_path)
            if not content:
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract required claims and check RBAC
            required_claims = RBACAuthorizer.extract_required_claims(content)
            RBACAuthorizer.check_rbac(token, required_claims, 'validate')
            
            # Perform validation
            success, errors, warnings = RunbookValidator.validate_runbook_content(runbook_path, content, env_vars)
            errors.extend(load_errors)
            warnings.extend(load_warnings)
            
            return {
                "success": success,
                "runbook": filename,
                "errors": errors,
                "warnings": warnings
            }
            
        except HTTPForbidden as e:
            # Log RBAC failure to runbook history
            try:
                config = Config.get_instance()
                HistoryManager.append_rbac_failure_history(
                    runbook_path, 
                    str(e), 
                    token.get('user_id', 'unknown'), 
                    'validate',
                    token,
                    breadcrumb,
                    config.config_items
                )
            except Exception as log_error:
                logger.error(f"Failed to log RBAC failure to history: {log_error}")
            raise
        
        except Exception as e:
            logger.error(f"Error validating runbook {filename}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to validate runbook: {str(e)}")
    
    def execute_runbook(self, filename: str, token: Dict, breadcrumb: Dict, env_vars: Optional[Dict[str, str]] = None, token_string: Optional[str] = None) -> Dict:
        """
        Execute a runbook.
        
        Args:
            filename: The runbook filename
            token: Token dictionary with user_id and claims
            breadcrumb: Breadcrumb dictionary for logging
            env_vars: Optional dictionary of environment variables to set
            token_string: Optional JWT token string for passing to scripts
            
        Returns:
            dict: Execution result with success, return_code, stdout, stderr, etc.
            
        Raises:
            HTTPNotFound: If runbook is not found
            HTTPForbidden: If RBAC check fails
        """
        runbook_path = self._resolve_runbook_path(filename)
        
        if not runbook_path.exists():
            raise HTTPNotFound(f"Runbook not found: {filename}")
        
        start_time = datetime.now(timezone.utc)
        config = Config.get_instance()
        
        try:
            # Extract recursion_stack from breadcrumb
            recursion_stack = breadcrumb.get('recursion_stack')
            # If None, treat as top-level execution (empty list for building new stack)
            if recursion_stack is None:
                recursion_stack = []
            
            # Initialize variables for history tracking
            validation_errors = []
            validation_warnings = []
            load_errors = []
            load_warnings = []
            validation_success = True
            
            # Recursion validation: Check if this runbook is already in the execution chain
            if filename in recursion_stack:
                error_msg = f"Recursion detected: Runbook {filename} already in execution chain: {recursion_stack}"
                logger.warning(f"Recursion attempt blocked: {error_msg}")
                return_code, stdout, stderr = 1, "", error_msg
            elif len(recursion_stack) >= config.MAX_RECURSION_DEPTH:
                # Recursion depth limit check
                error_msg = f"Recursion depth limit exceeded: {len(recursion_stack)} (max: {config.MAX_RECURSION_DEPTH})"
                logger.warning(f"Recursion depth limit exceeded: {error_msg}")
                return_code, stdout, stderr = 1, "", error_msg
            else:
                # Load runbook
                content, name, load_errors, load_warnings = RunbookParser.load_runbook(runbook_path)
                if not content:
                    raise HTTPInternalServerError("Failed to load runbook")
                
                # Extract required claims and check RBAC
                required_claims = RBACAuthorizer.extract_required_claims(content)
                RBACAuthorizer.check_rbac(token, required_claims, 'execute')
                
                # Validate runbook before execution (fail-fast)
                validation_success, validation_errors, validation_warnings = RunbookValidator.validate_runbook_content(runbook_path, content, env_vars)
                if not validation_success:
                    # Return validation errors as execution failure
                    error_msg = "\n".join(validation_errors)
                    return_code, stdout, stderr = 1, "", error_msg
                else:
                    # Extract script and execute
                    script = RunbookParser.extract_script(content)
                    if not script:
                        raise HTTPInternalServerError("Could not extract script from runbook")
                    
                    # Extract input paths from File System Requirements
                    fs_section = RunbookParser.extract_section(content, 'File System Requirements')
                    if fs_section:
                        requirements = RunbookParser.extract_file_requirements(fs_section)
                        input_paths = requirements.get('Input', [])
                    else:
                        input_paths = []
                    
                    # Build recursion stack for script (includes current runbook)
                    new_recursion_stack = recursion_stack + [filename]
                    # Update breadcrumb with new stack (for history/logging)
                    breadcrumb['recursion_stack'] = new_recursion_stack
                    
                    # Extract correlation_id from breadcrumb
                    correlation_id = breadcrumb.get('correlation_id')
                    
                    # Execute the script with system environment variables
                    return_code, stdout, stderr = ScriptExecutor.execute_script(
                        script, 
                        env_vars,
                        token_string=token_string,
                        correlation_id=correlation_id,
                        recursion_stack=new_recursion_stack,
                        input_paths=input_paths,
                        runbook_dir=runbook_path.parent
                    )
            
            finish_time = datetime.now(timezone.utc)
            
            # Collect errors/warnings for history
            errors = validation_errors if not validation_success else []
            warnings = validation_warnings
            errors.extend(load_errors)
            warnings.extend(load_warnings)
            
            # Append history
            HistoryManager.append_history(
                runbook_path,
                start_time,
                finish_time,
                return_code,
                'execute',
                stdout,
                stderr,
                token,
                breadcrumb,
                config.config_items,
                errors,
                warnings
            )
            
            # Reload content to parse last history entry for response
            with open(runbook_path, 'r', encoding='utf-8') as f:
                updated_content = f.read()
            
            # Parse last history entry for stdout/stderr
            parsed_stdout, parsed_stderr = RunbookParser.parse_last_history_entry(updated_content)
            
            return {
                "success": return_code == 0,
                "runbook": filename,
                "return_code": return_code,
                "stdout": parsed_stdout or stdout,
                "stderr": parsed_stderr or stderr,
                "errors": errors,
                "warnings": warnings
            }
            
        except HTTPForbidden as e:
            finish_time = datetime.now(timezone.utc)
            # Log RBAC failure to runbook history
            try:
                HistoryManager.append_rbac_failure_history(
                    runbook_path, 
                    str(e), 
                    token.get('user_id', 'unknown'), 
                    'execute',
                    token,
                    breadcrumb,
                    config.config_items
                )
            except Exception as log_error:
                logger.error(f"Failed to log RBAC failure to history: {log_error}")
            raise
        
        except Exception as e:
            finish_time = datetime.now(timezone.utc)
            logger.error(f"Error executing runbook {filename}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to execute runbook: {str(e)}")
    
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
                content, name, errors, warnings = RunbookParser.load_runbook(file_path)
                if content and name:
                    runbooks.append({
                        "filename": file_path.name,
                        "name": name,
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
            # Read file once
            with open(runbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract runbook name from content (reuse content instead of reading again)
            name = None
            import re
            match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                name = match.group(1).strip()
            
            return {
                "success": True,
                "filename": filename,
                "name": name or filename,
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
            content, name, errors, warnings = RunbookParser.load_runbook(runbook_path)
            if not content:
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract environment requirements
            env_section = RunbookParser.extract_section(content, 'Environment Requirements')
            if not env_section:
                return {
                    "success": True,
                    "filename": filename,
                    "required": [],
                    "available": [],
                    "missing": []
                }
            
            env_vars = RunbookParser.extract_yaml_block(env_section)
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
