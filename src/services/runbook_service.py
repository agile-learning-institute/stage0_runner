"""
Runbook service for business logic and RBAC.

Handles RBAC checks and runbook operations (validate/execute).
Includes RunbookRunner functionality merged from command.py.
"""
import os
import re
import subprocess
import json
import time
import uuid
import tempfile
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from ..flask_utils.exceptions import HTTPNotFound, HTTPForbidden, HTTPInternalServerError
from ..config.config import Config
import logging

logger = logging.getLogger(__name__)

# Regex pattern for valid environment variable names
# Must start with letter or underscore, followed by alphanumeric or underscore
ENV_VAR_NAME_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


class RunbookService:
    """
    Service class for Runbook domain operations.
    
    Handles:
    - RBAC authorization checks based on required_claims in runbook
    - Runbook validation
    - Runbook execution
    - Business logic for Runbook domain
    - Runbook parsing and execution (merged from RunbookRunner)
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
    
    def _load_runbook(self, runbook_path: Path) -> Tuple[Optional[str], Optional[str], List[str], List[str]]:
        """
        Load a runbook file and extract basic information.
        
        Args:
            runbook_path: Path to the runbook file
            
        Returns:
            tuple: (content, name, errors, warnings)
        """
        errors = []
        warnings = []
        
        if not runbook_path.exists():
            errors.append(f"Runbook file does not exist: {runbook_path}")
            return None, None, errors, warnings
        
        try:
            with open(runbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract runbook name from first H1
            match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Verify name matches filename
                expected_name = runbook_path.stem
                if name != expected_name:
                    warnings.append(
                        f"Runbook name '{name}' does not match filename '{expected_name}'"
                    )
            else:
                errors.append("Runbook must start with an H1 header containing the runbook name")
                return content, None, errors, warnings
            
            return content, name, errors, warnings
        except Exception as e:
            errors.append(f"Error reading runbook file: {e}")
            return None, None, errors, warnings
    
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content of a specific H1 section."""
        if not content:
            return None
            
        # Find the section header
        header_pattern = rf'^#\s+{re.escape(section_name)}\s*$'
        header_match = re.search(header_pattern, content, re.MULTILINE)
        if not header_match:
            return None
        
        # Get the position after the header
        start_pos = header_match.end()
        
        # Find the next H1 header or end of file
        next_header_pattern = r'^#\s+'
        next_match = re.search(next_header_pattern, content[start_pos:], re.MULTILINE)
        
        if next_match:
            # Content ends at the next header
            end_pos = start_pos + next_match.start()
            section_content = content[start_pos:end_pos].strip()
        else:
            # This is the last section, content goes to end of file
            section_content = content[start_pos:].strip()
        
        return section_content
    
    def _extract_yaml_block(self, section_content: str) -> Optional[Dict[str, str]]:
        """
        Extract YAML from a code block in section content using PyYAML.
        
        Args:
            section_content: Content of a section that may contain a YAML code block
            
        Returns:
            Dictionary of parsed YAML key-value pairs, or None if no YAML block found
        """
        if not section_content:
            return None
        
        pattern = r'```yaml\s*\n(.*?)```'
        match = re.search(pattern, section_content, re.DOTALL)
        if not match:
            return None
        
        yaml_content = match.group(1).strip()
        if not yaml_content:
            return {}  # Empty YAML block returns empty dict
        
        try:
            # Use PyYAML to parse the YAML content
            parsed_yaml = yaml.safe_load(yaml_content)
            
            # Handle different return types from YAML parser
            if parsed_yaml is None:
                return {}  # Empty or null YAML
            elif isinstance(parsed_yaml, dict):
                # Convert all values to strings for consistency with existing code
                result = {}
                for key, value in parsed_yaml.items():
                    if value is None:
                        result[str(key)] = ""
                    else:
                        result[str(key)] = str(value)
                return result if result else {}
            else:
                logger.warning(f"YAML block did not parse to a dictionary, got {type(parsed_yaml)}")
                return None
                
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML block: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing YAML block: {e}", exc_info=True)
            return None
    
    def _extract_required_claims(self, content: str) -> Optional[Dict[str, List[str]]]:
        """Extract required claims from Required Claims section."""
        claims_section = self._extract_section(content, 'Required Claims')
        if not claims_section:
            return None
        
        # Extract YAML block
        yaml_block = self._extract_yaml_block(claims_section)
        if not yaml_block:
            return None
        
        # Parse claims - convert values to lists if they're strings
        required_claims = {}
        for key, value in yaml_block.items():
            if isinstance(value, str):
                # If value contains commas, split into list
                if ',' in value:
                    required_claims[key] = [v.strip() for v in value.split(',')]
                else:
                    required_claims[key] = [value.strip()]
            elif isinstance(value, list):
                required_claims[key] = value
            else:
                required_claims[key] = [str(value)]
        
        return required_claims if required_claims else None
    
    def _extract_file_requirements(self, section_content: str) -> Dict[str, List[str]]:
        """
        Extract file system requirements from YAML block using PyYAML.
        
        Args:
            section_content: Content of File System Requirements section
            
        Returns:
            Dictionary with 'Input' and 'Output' keys, each containing a list of file paths
        """
        requirements = {'Input': [], 'Output': []}
        
        if not section_content:
            return requirements
        
        pattern = r'```yaml\s*\n(.*?)```'
        match = re.search(pattern, section_content, re.DOTALL)
        if not match:
            return requirements
        
        yaml_content = match.group(1).strip()
        if not yaml_content:
            return requirements
        
        try:
            # Use PyYAML to parse the YAML content
            parsed_yaml = yaml.safe_load(yaml_content)
            
            if parsed_yaml is None:
                return requirements
            
            if not isinstance(parsed_yaml, dict):
                logger.warning(f"File requirements YAML did not parse to a dictionary, got {type(parsed_yaml)}")
                return requirements
            
            # Extract Input and Output lists
            if 'Input' in parsed_yaml:
                input_value = parsed_yaml['Input']
                if isinstance(input_value, list):
                    requirements['Input'] = [str(item) for item in input_value if item is not None]
                elif input_value is not None:
                    # Single value, convert to list
                    requirements['Input'] = [str(input_value)]
            
            if 'Output' in parsed_yaml:
                output_value = parsed_yaml['Output']
                if isinstance(output_value, list):
                    requirements['Output'] = [str(item) for item in output_value if item is not None]
                elif output_value is not None:
                    # Single value, convert to list
                    requirements['Output'] = [str(output_value)]
            
            return requirements
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing file requirements YAML: {e}")
            return requirements
        except Exception as e:
            logger.error(f"Unexpected error parsing file requirements YAML: {e}", exc_info=True)
            return requirements
    
    def _extract_script(self, content: str) -> Optional[str]:
        """Extract the shell script from the Script section."""
        script_section = self._extract_section(content, 'Script')
        if not script_section:
            return None
        
        pattern = r'```sh\s*\n(.*?)```'
        match = re.search(pattern, script_section, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def _validate_runbook_content(self, runbook_path: Path, content: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the runbook structure and requirements.
        
        Returns:
            tuple: (success, errors, warnings)
        """
        errors = []
        warnings = []
        
        if not content:
            errors.append("Runbook content is empty")
            return False, errors, warnings
        
        # Check required sections
        required_sections = [
            'Documentation',
            'Environment Requirements',
            'File System Requirements',
            'Script',
            'History'
        ]
        # Required Claims is optional - if present, it must be valid
        
        for section in required_sections:
            section_content = self._extract_section(content, section)
            if section_content is None:
                errors.append(f"Missing required section: {section}")
            # History section can be empty, others cannot
            elif section != 'History' and not section_content:
                errors.append(f"Section '{section}' is empty")
        
        # Validate Environment Requirements
        env_section = self._extract_section(content, 'Environment Requirements')
        if env_section:
            env_vars = self._extract_yaml_block(env_section)
            if env_vars is not None:
                for var_name in env_vars.keys():
                    if var_name not in os.environ:
                        errors.append(f"Required environment variable not set: {var_name}")
            else:
                errors.append("Environment Requirements section must contain a YAML code block")
        else:
            errors.append("Missing Environment Requirements section")
        
        # Validate File System Requirements
        fs_section = self._extract_section(content, 'File System Requirements')
        if fs_section:
            requirements = self._extract_file_requirements(fs_section)
            for file_path in requirements.get('Input', []):
                # Resolve relative to runbook directory
                full_path = (runbook_path.parent / file_path).resolve()
                if not full_path.exists():
                    errors.append(f"Required input file does not exist: {file_path}")
            
            # Check output directories exist or can be created
            for dir_path in requirements.get('Output', []):
                path = Path(dir_path)
                if not path.exists():
                    # Check if parent exists and we can create it
                    if not path.parent.exists():
                        errors.append(f"Output directory parent does not exist: {dir_path}")
        else:
            errors.append("File System Requirements section must contain a YAML code block")
        
        # Validate Script section
        script = self._extract_script(content)
        if not script:
            errors.append("Script section must contain a sh code block")
        
        # Validate History section exists (empty content is valid)
        history_section = self._extract_section(content, 'History')
        if history_section is None:
            # Check if History header exists at all
            if not re.search(r'^#\s+History\s*$', content, re.MULTILINE):
                errors.append("Missing required section: History")
            # If header exists but extract_section returned None, that's also an error
            else:
                errors.append("History section found but could not extract content")
        # History section can be empty (no history entries yet)
        
        return len(errors) == 0, errors, warnings
    
    def _execute_script(self, runbook_path: Path, content: str, env_vars: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        """
        Execute the runbook script with resource limits (timeout, output size).
        
        Returns:
            tuple: (return_code, stdout, stderr)
        """
        config = Config.get_instance()
        timeout_seconds = config.SCRIPT_TIMEOUT_SECONDS
        max_output_bytes = config.MAX_OUTPUT_SIZE_BYTES
        
        # Validate resource limits - use Config defaults if invalid
        if timeout_seconds <= 0:
            default_timeout = config.get_default("SCRIPT_TIMEOUT_SECONDS")
            logger.warning(f"Invalid timeout value {timeout_seconds}, using Config default: {default_timeout}")
            timeout_seconds = default_timeout
        
        if max_output_bytes <= 0:
            default_max_output = config.get_default("MAX_OUTPUT_SIZE_BYTES")
            logger.warning(f"Invalid max_output_bytes value {max_output_bytes}, using Config default: {default_max_output}")
            max_output_bytes = default_max_output
        
        # Validate and sanitize environment variables
        original_env = {}
        sanitized_env_vars = {}
        
        if env_vars:
            for key, value in env_vars.items():
                # Validate environment variable name
                if not ENV_VAR_NAME_PATTERN.match(key):
                    logger.warning(f"Invalid environment variable name rejected: {key} (only alphanumeric and underscore allowed)")
                    return 1, "", f"ERROR: Invalid environment variable name: {key}. Variable names must start with a letter or underscore and contain only alphanumeric characters and underscores."
                
                # Validate value is string (convert if needed, but log it)
                if value is None:
                    logger.warning(f"Environment variable {key} has None value, converting to empty string")
                    value = ""
                elif not isinstance(value, str):
                    logger.warning(f"Environment variable {key} has non-string value type {type(value)}, converting to string")
                    value = str(value)
                
                # Sanitize value: remove control characters but preserve newlines and tabs for scripts
                # Control characters (0x00-0x1F) except newline (0x0A), tab (0x09), carriage return (0x0D)
                sanitized_value = ''.join(
                    char for char in value 
                    if ord(char) >= 32 or char in ['\n', '\t', '\r']
                )
                
                # Log if value was modified during sanitization
                if sanitized_value != value:
                    logger.warning(
                        f"Environment variable {key} value was sanitized: "
                        f"removed {len(value) - len(sanitized_value)} control characters"
                    )
                
                # Store original value for restoration
                original_env[key] = os.environ.get(key)
                sanitized_env_vars[key] = sanitized_value
                
                # Set the sanitized value in environment
                os.environ[key] = sanitized_value
                logger.debug(f"Set environment variable: {key} (value length: {len(sanitized_value)} bytes)")
        
        try:
            # Validate first
            success, errors, warnings = self._validate_runbook_content(runbook_path, content)
            if not success:
                return 1, "", "\n".join(errors)
            
            script = self._extract_script(content)
            if not script:
                return 1, "", "ERROR: Could not extract script from runbook"
            
            # Create isolated temporary directory for this execution (prevents path traversal)
            temp_exec_dir = None
            start_time = time.time()
            try:
                # Create a dedicated temp directory for this execution
                temp_exec_dir = Path(tempfile.mkdtemp(prefix=f'runbook-exec-{uuid.uuid4().hex[:8]}-'))
                temp_script = temp_exec_dir / 'temp.zsh'
                
                # Validate that the temp directory is actually a directory (security check)
                if not temp_exec_dir.exists() or not temp_exec_dir.is_dir():
                    raise HTTPInternalServerError(f"Failed to create temporary execution directory")
                
                # Create and write the script file
                with open(temp_script, 'w', encoding='utf-8') as f:
                    f.write(script)
                os.chmod(temp_script, 0o700)  # More restrictive: owner-only permissions
                
                # Execute the script with timeout and resource limits
                # Use temp_exec_dir as working directory for isolation
                logger.info(
                    f"Executing script with timeout={timeout_seconds}s, max_output={max_output_bytes} bytes, "
                    f"temp_dir={temp_exec_dir}"
                )
                
                try:
                    result = subprocess.run(
                        ['/bin/zsh', str(temp_script)],
                        capture_output=True,
                        text=True,
                        cwd=str(temp_exec_dir),  # Execute in isolated temp directory
                        timeout=timeout_seconds
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Apply output size limits
                    stdout = result.stdout or ""
                    stderr = result.stderr or ""
                    stdout_truncated = False
                    stderr_truncated = False
                    
                    # Check and truncate stdout if necessary
                    stdout_bytes = len(stdout.encode('utf-8'))
                    if stdout_bytes > max_output_bytes:
                        # Truncate to max size, preserving UTF-8 boundaries
                        stdout_encoded = stdout.encode('utf-8')
                        truncated_bytes = stdout_encoded[:max_output_bytes]
                        # Try to decode, if it fails remove last byte until valid
                        while True:
                            try:
                                stdout = truncated_bytes.decode('utf-8')
                                break
                            except UnicodeDecodeError:
                                truncated_bytes = truncated_bytes[:-1]
                        stdout_truncated = True
                        logger.warning(
                            f"Script stdout truncated from {stdout_bytes} bytes to {max_output_bytes} bytes "
                            f"(execution_time={execution_time:.2f}s)"
                        )
                    
                    # Check and truncate stderr if necessary
                    stderr_bytes = len(stderr.encode('utf-8'))
                    if stderr_bytes > max_output_bytes:
                        stderr_encoded = stderr.encode('utf-8')
                        truncated_bytes = stderr_encoded[:max_output_bytes]
                        while True:
                            try:
                                stderr = truncated_bytes.decode('utf-8')
                                break
                            except UnicodeDecodeError:
                                truncated_bytes = truncated_bytes[:-1]
                        stderr_truncated = True
                        logger.warning(
                            f"Script stderr truncated from {stderr_bytes} bytes to {max_output_bytes} bytes "
                            f"(execution_time={execution_time:.2f}s)"
                        )
                    
                    # Add truncation warnings to stderr if output was truncated
                    if stdout_truncated or stderr_truncated:
                        truncation_warning = (
                            f"\n[WARNING: Output truncated due to size limit ({max_output_bytes} bytes)]\n"
                        )
                        stderr = stderr + truncation_warning
                    
                    # Log resource usage
                    logger.info(
                        f"Script execution completed: return_code={result.returncode}, "
                        f"execution_time={execution_time:.2f}s, "
                        f"stdout_size={len(stdout.encode('utf-8'))} bytes, "
                        f"stderr_size={len(stderr.encode('utf-8'))} bytes"
                    )
                    
                    return result.returncode, stdout, stderr
                    
                except subprocess.TimeoutExpired:
                    execution_time = time.time() - start_time
                    error_msg = (
                        f"Script execution timed out after {timeout_seconds} seconds "
                        f"(actual execution time: {execution_time:.2f}s). "
                        f"The script was terminated to prevent resource exhaustion."
                    )
                    logger.warning(f"Script timeout: {error_msg}")
                    return 1, "", error_msg
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"ERROR: Failed to execute script: {e} (execution_time: {execution_time:.2f}s)"
                logger.error(error_msg, exc_info=True)
                return 1, "", error_msg
            finally:
                # Clean up temporary execution directory and all contents
                if temp_exec_dir and temp_exec_dir.exists():
                    try:
                        shutil.rmtree(temp_exec_dir)
                        logger.debug(f"Cleaned up temporary execution directory: {temp_exec_dir}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up temp directory {temp_exec_dir}: {cleanup_error}")
        finally:
            # Restore original environment variables
            for key, original_value in original_env.items():
                if original_value is None:
                    # Variable didn't exist before, remove it
                    os.environ.pop(key, None)
                    logger.debug(f"Restored environment: removed {key}")
                else:
                    # Restore original value
                    os.environ[key] = original_value
                    logger.debug(f"Restored environment: {key} = {original_value[:50] if len(str(original_value)) > 50 else original_value}...")
    
    def _append_history(self, runbook_path: Path, start_time: datetime, finish_time: datetime, 
                       return_code: int, operation: str, stdout: str, stderr: str, 
                       token: Dict, breadcrumb: Dict, config_items: List[Dict], 
                       errors: List[str] = None, warnings: List[str] = None):
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
    
    def _append_rbac_failure_history(self, runbook_path: Path, error_message: str, 
                                    user_id: str, operation: str, token: Dict, 
                                    breadcrumb: Dict, config_items: List[Dict]):
        """Append RBAC failure to the runbook history section as minified JSON."""
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
    
    def _parse_last_history_entry(self, content: str) -> Tuple[str, str]:
        """
        Parse the last history JSON entry from runbook content.
        
        Returns:
            tuple: (stdout, stderr)
        """
        if not content:
            return "", ""
        
        # Find all JSON lines after "# History" header
        history_section_start = content.find('# History')
        if history_section_start == -1:
            return "", ""
        
        # Get content after History header
        history_content = content[history_section_start:]
        
        # Extract all JSON lines (lines that start with {)
        json_lines = []
        for line in history_content.split('\n'):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                json_lines.append(line)
        
        if not json_lines:
            return "", ""
        
        # Parse the last JSON line
        try:
            last_entry = json.loads(json_lines[-1])
            stdout = last_entry.get('stdout', '')
            stderr = last_entry.get('stderr', '')
            return stdout, stderr
        except json.JSONDecodeError:
            logger.warning("Failed to parse last history entry JSON")
            return "", ""
    
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
            # Load runbook
            content, name, load_errors, load_warnings = self._load_runbook(runbook_path)
            if not content:
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract required claims and check RBAC
            required_claims = self._extract_required_claims(content)
            self._check_rbac(token, required_claims, 'validate')
            
            # Perform validation
            success, errors, warnings = self._validate_runbook_content(runbook_path, content)
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
                self._append_rbac_failure_history(
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
        
        start_time = datetime.now(timezone.utc)
        config = Config.get_instance()
        
        try:
            # Load runbook
            content, name, load_errors, load_warnings = self._load_runbook(runbook_path)
            if not content:
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract required claims and check RBAC
            required_claims = self._extract_required_claims(content)
            self._check_rbac(token, required_claims, 'execute')
            
            # Execute the script
            return_code, stdout, stderr = self._execute_script(runbook_path, content, env_vars)
            finish_time = datetime.now(timezone.utc)
            
            # Get validation errors/warnings for history
            success, errors, warnings = self._validate_runbook_content(runbook_path, content)
            errors.extend(load_errors)
            warnings.extend(load_warnings)
            
            # Append history
            self._append_history(
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
            parsed_stdout, parsed_stderr = self._parse_last_history_entry(updated_content)
            
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
                self._append_rbac_failure_history(
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
                content, name, errors, warnings = self._load_runbook(file_path)
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
            content, name, errors, warnings = self._load_runbook(runbook_path)
            if not content:
                raise HTTPInternalServerError("Failed to load runbook")
            
            # Extract environment requirements
            env_section = self._extract_section(content, 'Environment Requirements')
            if not env_section:
                return {
                    "success": True,
                    "filename": filename,
                    "required": [],
                    "available": [],
                    "missing": []
                }
            
            env_vars = self._extract_yaml_block(env_section)
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
