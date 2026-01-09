"""
Runbook validator for validating runbook structure and requirements.

Handles validation of runbook sections, environment variables, and file system requirements.
"""
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict

from .runbook_parser import RunbookParser


class RunbookValidator:
    """
    Validator for runbook structure and requirements.
    
    Handles:
    - Validating required sections exist
    - Validating environment variables are set
    - Validating file system requirements
    - Validating script section exists
    """
    
    @staticmethod
    def validate_runbook_content(runbook_path: Path, content: str, env_vars: Optional[Dict[str, str]] = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the runbook structure and requirements.
        
        Args:
            runbook_path: Path to the runbook file
            content: Runbook content string
            env_vars: Optional dict of environment variables to check (merged with os.environ)
            
        Returns:
            tuple: (success, errors, warnings)
        """
        # Merge provided env_vars with os.environ for validation
        env_to_check = dict(os.environ)
        if env_vars:
            env_to_check.update(env_vars)
        errors = []
        warnings = []
        
        if not content:
            errors.append("Runbook content is empty")
            return False, errors, warnings
        
        # Check required sections
        required_sections = [
            'Environment Requirements',
            'File System Requirements',
            'Script',
            'History'
        ]
        # Required Claims is optional - if present, it must be valid
        
        for section in required_sections:
            section_content = RunbookParser.extract_section(content, section)
            if section_content is None:
                errors.append(f"Missing required section: {section}")
            # History section can be empty, others cannot
            elif section != 'History' and not section_content:
                errors.append(f"Section '{section}' is empty")
        
        # Validate Environment Requirements
        env_section = RunbookParser.extract_section(content, 'Environment Requirements')
        if env_section:
            required_env_vars = RunbookParser.extract_yaml_block(env_section)
            if required_env_vars is not None:
                for var_name in required_env_vars.keys():
                    if var_name not in env_to_check:
                        errors.append(f"Required environment variable not set: {var_name}")
            else:
                errors.append("Environment Requirements section must contain a YAML code block")
        else:
            errors.append("Missing Environment Requirements section")
        
        # Validate File System Requirements
        fs_section = RunbookParser.extract_section(content, 'File System Requirements')
        if fs_section:
            requirements = RunbookParser.extract_file_requirements(fs_section)
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
        script = RunbookParser.extract_script(content)
        if not script:
            errors.append("Script section must contain a sh code block")
        
        # Validate History section exists (empty content is valid)
        history_section = RunbookParser.extract_section(content, 'History')
        if history_section is None:
            # Check if History header exists at all
            if not re.search(r'^#\s+History\s*$', content, re.MULTILINE):
                errors.append("Missing required section: History")
            # If header exists but extract_section returned None, that's also an error
            else:
                errors.append("History section found but could not extract content")
        # History section can be empty (no history entries yet)
        
        return len(errors) == 0, errors, warnings

