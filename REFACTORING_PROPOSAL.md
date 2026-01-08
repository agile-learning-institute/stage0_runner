# RunbookService Refactoring Proposal

## Current State

`runbook_service.py` is 1,074 lines and handles multiple concerns:
- Runbook parsing (markdown extraction)
- Runbook validation
- Script execution with resource limits
- History management
- RBAC authorization
- Service orchestration

## Proposed Structure

### 1. `runbook_parser.py` - Runbook Parsing (~200 lines)
**Responsibility**: Extract content from markdown runbook files

**Methods**:
- `load_runbook(runbook_path: Path) -> Tuple[Optional[str], Optional[str], List[str], List[str]]`
- `extract_section(content: str, section_name: str) -> Optional[str]`
- `extract_yaml_block(section_content: str) -> Optional[Dict[str, str]]`
- `extract_required_claims(content: str) -> Optional[Dict[str, List[str]]]`
- `extract_file_requirements(section_content: str) -> Dict[str, List[str]]`
- `extract_script(content: str) -> Optional[str]`
- `parse_last_history_entry(content: str) -> Tuple[str, str]`

**Dependencies**: `yaml`, `re`, `Path`

### 2. `runbook_validator.py` - Runbook Validation (~150 lines)
**Responsibility**: Validate runbook structure and requirements

**Methods**:
- `validate_runbook_content(runbook_path: Path, content: str, parser: RunbookParser) -> Tuple[bool, List[str], List[str]]`

**Dependencies**: `RunbookParser`, `Path`, `os`

### 3. `script_executor.py` - Script Execution (~250 lines)
**Responsibility**: Execute scripts with resource limits, isolation, and environment variable management

**Methods**:
- `execute_script(script: str, env_vars: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]`
- `_validate_env_var_name(name: str) -> bool`
- `_sanitize_env_var_value(value: str) -> str`
- `_create_temp_execution_dir() -> Path`
- `_truncate_output(output: str, max_bytes: int) -> Tuple[str, bool]`

**Dependencies**: `subprocess`, `tempfile`, `Config`, `Path`, `os`

### 4. `history_manager.py` - History Management (~150 lines)
**Responsibility**: Manage execution history in runbook files

**Methods**:
- `append_history(runbook_path: Path, start_time: datetime, finish_time: datetime, 
                 return_code: int, operation: str, stdout: str, stderr: str,
                 token: Dict, breadcrumb: Dict, config_items: List[Dict],
                 errors: List[str] = None, warnings: List[str] = None) -> None`
- `append_rbac_failure_history(runbook_path: Path, error_message: str,
                               user_id: str, operation: str, token: Dict,
                               breadcrumb: Dict, config_items: List[Dict]) -> None`

**Dependencies**: `json`, `datetime`, `Path`, `logging`

### 5. `rbac_authorizer.py` - RBAC Authorization (~100 lines)
**Responsibility**: Handle role-based access control checks

**Methods**:
- `check_rbac(token: Dict, required_claims: Optional[Dict[str, List[str]]], operation: str) -> bool`
- `extract_required_claims(content: str, parser: RunbookParser) -> Optional[Dict[str, List[str]]]`

**Dependencies**: `RunbookParser`, `HTTPForbidden`

### 6. `runbook_service.py` - Service Orchestration (~300 lines)
**Responsibility**: Orchestrate all components to provide the public API

**Public Methods** (unchanged):
- `validate_runbook(filename: str, token: Dict, breadcrumb: Dict) -> Dict`
- `execute_runbook(filename: str, token: Dict, breadcrumb: Dict, env_vars: Optional[Dict[str, str]] = None) -> Dict`
- `list_runbooks(token: Dict, breadcrumb: Dict) -> Dict`
- `get_runbook(filename: str, token: Dict, breadcrumb: Dict) -> Dict`
- `get_required_env(filename: str, token: Dict, breadcrumb: Dict) -> Dict`

**Dependencies**: All other modules

## Benefits

1. **Single Responsibility**: Each module has one clear purpose
2. **Testability**: Each component can be tested independently
3. **Maintainability**: Easier to locate and fix bugs
4. **Reusability**: Components can be reused in other contexts
5. **Readability**: Smaller, focused files are easier to understand

## Migration Strategy

1. Create new modules with extracted code
2. Update `RunbookService` to use new modules (composition)
3. Run existing tests to ensure compatibility
4. Gradually refactor tests to test components independently
5. Remove old code once migration is complete

## File Structure

```
src/services/
├── runbook_service.py      # Main service (orchestrator)
├── runbook_parser.py       # Markdown parsing
├── runbook_validator.py    # Validation logic
├── script_executor.py      # Script execution
├── history_manager.py      # History management
└── rbac_authorizer.py      # RBAC checks
```

## Example Usage (After Refactoring)

```python
# In runbook_service.py
class RunbookService:
    def __init__(self, runbooks_dir: str):
        self.runbooks_dir = Path(runbooks_dir).resolve()
        self.parser = RunbookParser()
        self.validator = RunbookValidator(self.parser)
        self.executor = ScriptExecutor()
        self.history = HistoryManager()
        self.rbac = RBACAuthorizer(self.parser)
    
    def execute_runbook(self, filename: str, token: Dict, breadcrumb: Dict, 
                       env_vars: Optional[Dict[str, str]] = None) -> Dict:
        runbook_path = self._resolve_runbook_path(filename)
        content, name, load_errors, load_warnings = self.parser.load_runbook(runbook_path)
        
        # Check RBAC
        required_claims = self.rbac.extract_required_claims(content)
        self.rbac.check_rbac(token, required_claims, 'execute')
        
        # Execute
        script = self.parser.extract_script(content)
        return_code, stdout, stderr = self.executor.execute_script(script, env_vars)
        
        # Append history
        self.history.append_history(...)
        
        return {...}
```

