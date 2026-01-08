"""
Runbook parser for extracting content from markdown runbook files.

Handles parsing of markdown sections, YAML blocks, scripts, and history entries.
"""
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RunbookParser:
    """
    Parser for extracting content from markdown runbook files.
    
    Handles:
    - Loading runbook files
    - Extracting markdown sections
    - Parsing YAML blocks
    - Extracting scripts
    - Parsing history entries
    """
    
    @staticmethod
    def load_runbook(runbook_path: Path) -> Tuple[Optional[str], Optional[str], List[str], List[str]]:
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
    
    @staticmethod
    def extract_section(content: str, section_name: str) -> Optional[str]:
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
    
    @staticmethod
    def extract_yaml_block(section_content: str) -> Optional[Dict[str, str]]:
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
    
    @staticmethod
    def extract_required_claims(content: str) -> Optional[Dict[str, List[str]]]:
        """Extract required claims from Required Claims section."""
        claims_section = RunbookParser.extract_section(content, 'Required Claims')
        if not claims_section:
            return None
        
        # Extract YAML block
        yaml_block = RunbookParser.extract_yaml_block(claims_section)
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
    
    @staticmethod
    def extract_file_requirements(section_content: str) -> Dict[str, List[str]]:
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
    
    @staticmethod
    def extract_script(content: str) -> Optional[str]:
        """Extract the shell script from the Script section."""
        script_section = RunbookParser.extract_section(content, 'Script')
        if not script_section:
            return None
        
        pattern = r'```sh\s*\n(.*?)```'
        match = re.search(pattern, script_section, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    @staticmethod
    def parse_last_history_entry(content: str) -> Tuple[str, str]:
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

