"""
History manager for managing execution history in runbook files.

Handles appending execution history and RBAC failure history to runbook files.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Manager for execution history in runbook files.
    
    Handles:
    - Appending execution history as minified JSON
    - Appending RBAC failure history
    - Logging history entries
    """
    
    @staticmethod
    def append_history(runbook_path: Path, start_time: datetime, finish_time: datetime, 
                      return_code: int, operation: str, stdout: str, stderr: str, 
                      token: Dict, breadcrumb: Dict, config_items: List[Dict], 
                      errors: List[str] = None, warnings: List[str] = None) -> None:
        """
        Append execution history to the runbook file as minified JSON.
        
        Args:
            runbook_path: Path to the runbook file
            start_time: Start timestamp
            finish_time: Finish timestamp
            return_code: Return code from execution
            operation: Operation name (e.g., 'execute', 'validate')
            stdout: Standard output
            stderr: Standard error
            token: Token dictionary with roles
            breadcrumb: Breadcrumb dictionary
            config_items: Config items from Config singleton
            errors: List of errors (optional)
            warnings: List of warnings (optional)
        """
        # Format timestamps as ISO 8601 with Z timezone
        start_timestamp = start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        finish_timestamp = finish_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Add roles to breadcrumb (preserve existing breadcrumb structure)
        at_time_value = breadcrumb.get('at_time', '')
        if hasattr(at_time_value, 'isoformat'):
            at_time_str = at_time_value.isoformat()
        elif isinstance(at_time_value, str):
            at_time_str = at_time_value
        else:
            at_time_str = str(at_time_value)
        
        breadcrumb_with_roles = {
            **breadcrumb,
            "roles": token.get('roles', []),
            "at_time": at_time_str
        }
        
        # Build history JSON
        history_json = {
            "start_timestamp": start_timestamp,
            "finish_timestamp": finish_timestamp,
            "return_code": return_code,
            "operation": operation,
            "breadcrumb": breadcrumb_with_roles,
            "config_items": config_items,
            "stdout": stdout,
            "stderr": stderr,
            "errors": errors or [],
            "warnings": warnings or []
        }
        
        # Minify JSON (single line, no whitespace)
        minified_json = json.dumps(history_json, separators=(',', ':'))
        
        # Log the history JSON
        logger.log(logging.INFO, minified_json)
        
        # Append to file
        with open(runbook_path, 'a', encoding='utf-8') as f:
            f.write('\n' + minified_json)
    
    @staticmethod
    def append_rbac_failure_history(runbook_path: Path, error_message: str, 
                                   user_id: str, operation: str, token: Dict, 
                                   breadcrumb: Dict, config_items: List[Dict]) -> None:
        """
        Append RBAC failure to the runbook history section as minified JSON.
        
        Args:
            runbook_path: Path to the runbook file
            error_message: Error message describing the RBAC failure
            user_id: User ID that attempted the operation
            operation: Operation name (e.g., 'execute', 'validate')
            token: Token dictionary with roles
            breadcrumb: Breadcrumb dictionary
            config_items: Config items from Config singleton
        """
        timestamp = datetime.now(timezone.utc)
        
        # Add roles to breadcrumb (preserve existing breadcrumb structure)
        at_time_value = breadcrumb.get('at_time', '')
        if hasattr(at_time_value, 'isoformat'):
            at_time_str = at_time_value.isoformat()
        elif isinstance(at_time_value, str):
            at_time_str = at_time_value
        else:
            at_time_str = str(at_time_value)
        
        breadcrumb_with_roles = {
            **breadcrumb,
            "roles": token.get('roles', []),
            "at_time": at_time_str
        }
        
        history_json = {
            "start_timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "finish_timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
            "return_code": 403,
            "operation": operation,
            "breadcrumb": breadcrumb_with_roles,
            "config_items": config_items,
            "stdout": "",
            "stderr": "",
            "errors": [f"RBAC Failure: Access denied for user {user_id}. {error_message}"],
            "warnings": []
        }
        
        # Minify JSON
        minified_json = json.dumps(history_json, separators=(',', ':'))
        
        # Log the history JSON
        logger.log(logging.INFO, minified_json)
        
        # Append to file
        with open(runbook_path, 'a', encoding='utf-8') as f:
            f.write('\n' + minified_json)

