#!/usr/bin/env python3
"""
Stage0 Runbook Runner

This utility validates and executes runbooks. A runbook is a markdown file
with specific structure requirements as defined in RUNBOOK.md.
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RunbookRunner:
    """Handles validation and execution of runbooks."""
    
    def __init__(self, runbook_path: str):
        self.runbook_path = Path(runbook_path).resolve()
        self.runbook_content = None
        self.runbook_name = None
        self.errors = []
        self.warnings = []
    
    def load_runbook(self) -> bool:
        """Load the runbook file."""
        if not self.runbook_path.exists():
            self.errors.append(f"Runbook file does not exist: {self.runbook_path}")
            return False
        
        try:
            with open(self.runbook_path, 'r', encoding='utf-8') as f:
                self.runbook_content = f.read()
            
            # Extract runbook name from first H1
            match = re.match(r'^#\s+(.+)$', self.runbook_content, re.MULTILINE)
            if match:
                self.runbook_name = match.group(1).strip()
                # Verify name matches filename
                expected_name = self.runbook_path.stem
                if self.runbook_name != expected_name:
                    self.warnings.append(
                        f"Runbook name '{self.runbook_name}' does not match filename '{expected_name}'"
                    )
            else:
                self.errors.append("Runbook must start with an H1 header containing the runbook name")
                return False
            
            return True
        except Exception as e:
            self.errors.append(f"Error reading runbook file: {e}")
            return False
    
    def extract_section(self, section_name: str) -> Optional[str]:
        """Extract content of a specific H1 section."""
        # Find the section header
        header_pattern = rf'^#\s+{re.escape(section_name)}\s*$'
        header_match = re.search(header_pattern, self.runbook_content, re.MULTILINE)
        if not header_match:
            return None
        
        # Get the position after the header
        start_pos = header_match.end()
        
        # Find the next H1 header or end of file
        next_header_pattern = r'^#\s+'
        next_match = re.search(next_header_pattern, self.runbook_content[start_pos:], re.MULTILINE)
        
        if next_match:
            # Content ends at the next header
            end_pos = start_pos + next_match.start()
            content = self.runbook_content[start_pos:end_pos].strip()
        else:
            # This is the last section, content goes to end of file
            content = self.runbook_content[start_pos:].strip()
        
        return content
    
    def extract_yaml_block(self, section_content: str) -> Optional[Dict[str, str]]:
        """Extract YAML from a code block in section content."""
        if not section_content:
            return None
        pattern = r'```yaml\s*\n(.*?)```'
        match = re.search(pattern, section_content, re.DOTALL)
        if match:
            yaml_content = match.group(1).strip()
            # Simple YAML parsing for key: value pairs
            env_vars = {}
            for line in yaml_content.split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        env_vars[key] = value
            return env_vars if env_vars else {}  # Return empty dict if no vars found
        return None
    
    def extract_required_claims(self) -> Optional[Dict[str, List[str]]]:
        """Extract required claims from Required Claims section."""
        claims_section = self.extract_section('Required Claims')
        if not claims_section:
            return None
        
        # Extract YAML block
        yaml_block = self.extract_yaml_block(claims_section)
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
    
    def extract_file_requirements(self, section_content: str) -> Dict[str, List[str]]:
        """Extract file system requirements from YAML block."""
        requirements = {'Input': [], 'Output': []}
        pattern = r'```yaml\s*\n(.*?)```'
        match = re.search(pattern, section_content, re.DOTALL)
        if match:
            yaml_content = match.group(1).strip()
            current_section = None
            for line in yaml_content.split('\n'):
                line = line.strip()
                if line.startswith('Input:'):
                    current_section = 'Input'
                elif line.startswith('Output:'):
                    current_section = 'Output'
                elif line.startswith('-') and current_section:
                    file_path = line[1:].strip()
                    requirements[current_section].append(file_path)
        return requirements
    
    def extract_script(self) -> Optional[str]:
        """Extract the shell script from the Script section."""
        script_section = self.extract_section('Script')
        if not script_section:
            return None
        
        pattern = r'```sh\s*\n(.*?)```'
        match = re.search(pattern, script_section, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def validate(self) -> bool:
        """Validate the runbook structure and requirements."""
        self.errors = []
        self.warnings = []
        
        if not self.load_runbook():
            return False
        
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
            section_content = self.extract_section(section)
            if section_content is None:
                self.errors.append(f"Missing required section: {section}")
            # History section can be empty, others cannot
            elif section != 'History' and not section_content:
                self.errors.append(f"Section '{section}' is empty")
        
        # Validate Environment Requirements
        env_section = self.extract_section('Environment Requirements')
        if env_section:
            env_vars = self.extract_yaml_block(env_section)
            if env_vars is not None:
                for var_name in env_vars.keys():
                    if var_name not in os.environ:
                        self.errors.append(f"Required environment variable not set: {var_name}")
            else:
                self.errors.append("Environment Requirements section must contain a YAML code block")
        else:
            self.errors.append("Missing Environment Requirements section")
        
        # Validate File System Requirements
        fs_section = self.extract_section('File System Requirements')
        if fs_section:
            requirements = self.extract_file_requirements(fs_section)
            for file_path in requirements.get('Input', []):
                # Resolve relative to runbook directory
                full_path = (self.runbook_path.parent / file_path).resolve()
                if not full_path.exists():
                    self.errors.append(f"Required input file does not exist: {file_path}")
            
            # Check output directories exist or can be created
            for dir_path in requirements.get('Output', []):
                path = Path(dir_path)
                if not path.exists():
                    # Check if parent exists and we can create it
                    if not path.parent.exists():
                        self.errors.append(f"Output directory parent does not exist: {dir_path}")
        else:
            self.errors.append("File System Requirements section must contain a YAML code block")
        
        # Validate Script section
        script = self.extract_script()
        if not script:
            self.errors.append("Script section must contain a sh code block")
        
        # Validate History section exists (empty content is valid)
        history_section = self.extract_section('History')
        if history_section is None:
            # Check if History header exists at all
            if not re.search(r'^#\s+History\s*$', self.runbook_content, re.MULTILINE):
                self.errors.append("Missing required section: History")
            # If header exists but extract_section returned None, that's also an error
            else:
                self.errors.append("History section found but could not extract content")
        # History section can be empty (no history entries yet)
        
        return len(self.errors) == 0
    
    def execute(self) -> int:
        """Execute the runbook script."""
        # Fail-fast validation
        if not self.validate():
            print("Validation failed. Cannot execute runbook.", file=sys.stderr)
            for error in self.errors:
                print(f"  ERROR: {error}", file=sys.stderr)
            return 1
        
        script = self.extract_script()
        if not script:
            print("ERROR: Could not extract script from runbook", file=sys.stderr)
            return 1
        
        # Create temporary script file
        temp_script = self.runbook_path.parent / 'temp.zsh'
        try:
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(script)
            os.chmod(temp_script, 0o755)
            
            # Execute the script
            start_time = datetime.now()
            result = subprocess.run(
                ['/bin/zsh', str(temp_script)],
                capture_output=True,
                text=True,
                cwd=self.runbook_path.parent
            )
            end_time = datetime.now()
            
            # Append execution history to runbook
            self.append_history(result, start_time, end_time)
            
            return result.returncode
        except Exception as e:
            print(f"ERROR: Failed to execute script: {e}", file=sys.stderr)
            return 1
        finally:
            # Clean up temp script
            if temp_script.exists():
                temp_script.unlink()
    
    def append_history(self, result: subprocess.CompletedProcess, start_time: datetime, end_time: datetime):
        """Append execution history to the runbook file."""
        timestamp = start_time.strftime('%Y-%m-%dt%H:%M:%S.%f')[:-3]  # Remove last 3 digits of microseconds
        completed = end_time.strftime('%Y-%m-%dt%H:%M:%S.%f')[:-3]
        
        # Format stdout and stderr in code blocks
        stdout_content = result.stdout if result.stdout else ""
        stderr_content = result.stderr if result.stderr else ""
        
        history_entry = f"""
## {timestamp}
- Completed: {completed}
- Return Code: {result.returncode}

### stdout
```
{stdout_content}
```

### stderr
```
{stderr_content}
```
"""
        
        # Append to file
        with open(self.runbook_path, 'a', encoding='utf-8') as f:
            f.write(history_entry)
    
    def append_rbac_failure_history(self, error_message: str, user_id: str, operation: str):
        """Append RBAC failure to the runbook history section."""
        timestamp = datetime.now().strftime('%Y-%m-%dt%H:%M:%S.%f')[:-3]
        
        history_entry = f"""
## {timestamp}
- Operation: {operation}
- Return Code: 403
- RBAC Failure: Access denied for user {user_id}

### error
```
{error_message}
```
"""
        
        # Append to file
        with open(self.runbook_path, 'a', encoding='utf-8') as f:
            f.write(history_entry)


def main():
    """Main entry point for the command."""
    parser = argparse.ArgumentParser(
        description='Stage0 Runbook Runner - Validate and execute runbooks'
    )
    parser.add_argument(
        'action',
        choices=['validate', 'execute', 'serve'],
        help='Action to perform: validate, execute, or serve (API server)'
    )
    parser.add_argument(
        '--runbook',
        default=os.environ.get('RUNBOOK', './samples/runbooks/SimpleRunbook.md'),
        help='Path to runbook file (or set RUNBOOK environment variable)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('API_PORT', '8083')),
        help='Port for API server (default: 8083, or API_PORT env var)'
    )
    parser.add_argument(
        '--runbooks-dir',
        default=os.environ.get('RUNBOOKS_DIR', './samples/runbooks'),
        help='Directory containing runbooks (default: ./samples/runbooks, or RUNBOOKS_DIR env var)'
    )
    
    args = parser.parse_args()
    
    if args.action == 'serve':
        from server import create_app
        app = create_app(args.runbooks_dir)
        port = args.port
        print(f"Starting runbook API server on http://0.0.0.0:{port}")
        print(f"Runbooks directory: {Path(args.runbooks_dir).resolve()}")
        print(f"API endpoints available at http://localhost:{port}/api/")
        print(f"API Explorer available at http://localhost:{port}/docs/explorer.html")
        app.run(host='0.0.0.0', port=port, debug=False)
        return
    
    if not args.runbook:
        print("ERROR: Runbook path not provided. Use --runbook or set RUNBOOK environment variable.", file=sys.stderr)
        sys.exit(1)
    
    runner = RunbookRunner(args.runbook)
    
    if args.action == 'validate':
        success = runner.validate()
        if runner.errors:
            for error in runner.errors:
                print(f"ERROR: {error}", file=sys.stderr)
        if runner.warnings:
            for warning in runner.warnings:
                print(f"WARNING: {warning}", file=sys.stderr)
        if success:
            print(f"✓ Runbook validation passed: {args.runbook}", file=sys.stdout)
        sys.exit(0 if success else 1)
    elif args.action == 'execute':
        return_code = runner.execute()
        sys.exit(return_code)


if __name__ == '__main__':
    main()

