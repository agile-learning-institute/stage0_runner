"""
History manager for managing execution history in runbook files.

Design Intent:
- Full detailed history (including breadcrumbs, config, etc.) is logged to application logs
- Only core execution info (timestamp, exit code, stdout, stderr) is written to the markdown file
- Markdown history is for human verification only and is not persisted across container restarts
- Users requiring persistent history should collect it from application logs

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
    
    Design Intent:
    - Full detailed history is logged to application logs (for persistence/analysis)
    - Only core info is written to markdown (timestamp, exit code, stdout, stderr) for human verification
    - Markdown history is ephemeral (lost on container restart) - use logs for persistence
    
    Handles:
    - Logging full execution history as JSON
    - Appending human-readable markdown history to runbook file
    - Appending RBAC failure history
    """
    
    @staticmethod
    def append_history(runbook_path: Path, start_time: datetime, finish_time: datetime, 
                      return_code: int, operation: str, stdout: str, stderr: str, 
                      token: Dict, breadcrumb: Dict, config_items: List[Dict], 
                      errors: List[str] = None, warnings: List[str] = None) -> None:
        """
        Append execution history to the runbook file.
        
        Full detailed history (including breadcrumbs, config, etc.) is logged to application logs.
        Only core execution info (timestamp, exit code, stdout, stderr) is written to markdown.
        
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
        
        # Build full history JSON for logging (includes all details)
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
        
        # Minify JSON for logging (single line, no whitespace)
        minified_json = json.dumps(history_json, separators=(',', ':'))
        
        # Log the full history JSON to application logs (for persistence/analysis)
        logger.log(logging.INFO, minified_json)
        
        # Format human-readable markdown for file (core info only)
        # Escape markdown code fence delimiters in stdout/stderr
        stdout_escaped = stdout.replace('```', '\\`\\`\\`')
        stderr_escaped = stderr.replace('```', '\\`\\`\\`')
        
        markdown_history = f"\n### {finish_timestamp} | Exit Code: {return_code}\n\n"
        if stdout_escaped:
            markdown_history += f"**Stdout:**\n```\n{stdout_escaped}\n```\n\n"
        if stderr_escaped:
            markdown_history += f"**Stderr:**\n```\n{stderr_escaped}\n```\n"
        
        # Append human-readable markdown to file
        with open(runbook_path, 'a', encoding='utf-8') as f:
            f.write(markdown_history)
    
    @staticmethod
    def append_rbac_failure_history(runbook_path: Path, error_message: str, 
                                   user_id: str, operation: str, token: Dict, 
                                   breadcrumb: Dict, config_items: List[Dict]) -> None:
        """
        Append RBAC failure to the runbook history section.
        
        Full detailed history is logged to application logs.
        Only core info (timestamp, exit code, error message) is written to markdown.
        
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
        timestamp_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
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
        
        # Build full history JSON for logging (includes all details)
        history_json = {
            "start_timestamp": timestamp_str,
            "finish_timestamp": timestamp_str,
            "return_code": 403,
            "operation": operation,
            "breadcrumb": breadcrumb_with_roles,
            "config_items": config_items,
            "stdout": "",
            "stderr": "",
            "errors": [f"RBAC Failure: Access denied for user {user_id}. {error_message}"],
            "warnings": []
        }
        
        # Minify JSON for logging
        minified_json = json.dumps(history_json, separators=(',', ':'))
        
        # Log the full history JSON to application logs (for persistence/analysis)
        logger.log(logging.INFO, minified_json)
        
        # Format human-readable markdown for file (core info only)
        error_msg = f"RBAC Failure: Access denied for user {user_id}. {error_message}"
        error_msg_escaped = error_msg.replace('```', '\\`\\`\\`')
        
        markdown_history = f"\n### {timestamp_str} | Exit Code: 403\n\n"
        markdown_history += f"**Error:**\n```\n{error_msg_escaped}\n```\n"
        
        # Append human-readable markdown to file
        with open(runbook_path, 'a', encoding='utf-8') as f:
            f.write(markdown_history)

