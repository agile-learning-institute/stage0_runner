# Refactor Plan: Input File Support and Output Removal

## Overview

This refactor plan outlines changes to:
1. **Remove Output section support** - The Output list in File System Requirements is no longer needed
2. **Copy Input files/folders to execution directory** - Make input files available to scripts in the temporary execution folder
3. **Verify security and isolation** - Ensure thread safety, path restrictions, and proper cleanup

## Context

Currently:
- Input files are validated for existence but are **not copied** to the temporary execution directory
- Scripts execute in an isolated temporary directory but cannot access input files (using `./file` fails)
- Output section exists but serves no functional purpose
- Execution uses `cwd=temp_exec_dir` which restricts script access to that directory
- Cleanup uses `shutil.rmtree(temp_exec_dir)` in a finally block

## Goals

1. Remove all Output section handling (parser, validator, tests, documentation)
2. Copy Input files/folders to the temporary execution directory before script execution
3. Ensure Input can handle both files and directories
4. Verify multi-threaded safety of temporary directory creation
5. Verify execution isolation (scripts cannot access `/` or `../something`)
6. Verify cleanup removes directory and all sub-folders

---

## Phase 1: Remove Output Section Support ✅ COMPLETED

### 1.1 Update RunbookParser (`src/services/runbook_parser.py`) ✅

**Change `extract_file_requirements` method:**
- Remove `'Output'` key from the `requirements` dictionary
- Remove all Output parsing logic (lines ~244-250)
- Update return type documentation to only mention Input
- Update method docstring to remove Output references

**Files to modify:**
- `src/services/runbook_parser.py` (method `extract_file_requirements`)

### 1.2 Update RunbookValidator (`src/services/runbook_validator.py`) ✅

**Change `validate_runbook_content` method:**
- Remove Output validation logic (lines ~89-95)
- Remove `requirements.get('Output', [])` checks
- Update method docstring if it mentions Output validation

**Files to modify:**
- `src/services/runbook_validator.py` (method `validate_runbook_content`)

### 1.3 Update Documentation ✅

**Update RUNBOOK.md:**
- Remove Output from the File System Requirements section example
- Update section description to remove Output references
- Update "Execution Processing" section if it mentions Output

**Files to modify:**
- `RUNBOOK.md`

### 1.4 Update Tests ✅

**Remove Output-related test assertions:**
- `test/unit/services/test_runbook_parser.py` (or similar) - Remove Output assertions
- `test/unit/services/test_runbook_validator.py` - Remove Output validation tests
- `test/unit/services/test_runbook_service.py` - Remove Output from test runbook templates
- `test/integration/test_integration.py` - Update test runbooks if they reference Output
- `test/e2e/test_e2e.py` - Update test runbooks if they reference Output

**Files to modify:**
- All test files that create test runbooks with Output sections
- All test files that assert Output parsing/validation

### 1.5 Update Sample Runbooks ✅

**Remove Output sections from sample runbooks:**
- `samples/runbooks/Runbook.md`
- `samples/runbooks/SimpleRunbook.md`
- `samples/runbooks/ParentRunbook.md`
- Any other sample runbooks

**Files to modify:**
- All `*.md` files in `samples/runbooks/` directory

---

## Phase 2: Implement Input File Copying

### 2.1 Add Input Copy Function to ScriptExecutor

**Create new method `_copy_input_files` in `ScriptExecutor` class:**

```python
@staticmethod
def _copy_input_files(
    input_paths: List[str],
    runbook_dir: Path,
    temp_exec_dir: Path
) -> List[str]:
    """
    Copy input files/folders to temporary execution directory.
    
    Args:
        input_paths: List of input file/folder paths (relative to runbook directory)
        runbook_dir: Path to the directory containing the runbook
        temp_exec_dir: Temporary execution directory where files should be copied
        
    Returns:
        List of error messages (empty if successful)
        
    Raises:
        HTTPInternalServerError: If copying fails critically
    """
```

**Implementation requirements:**
- Validate input paths to prevent directory traversal attacks
  - Resolve paths relative to `runbook_dir`
  - Verify resolved path is within `runbook_dir` (use `Path.resolve()` and check `is_relative_to()` or compare parents)
  - Reject absolute paths that don't start with `runbook_dir`
  - Reject paths with `..` components that escape `runbook_dir`
- For each input path:
  - Resolve source path: `source_path = (runbook_dir / input_path).resolve()`
  - Validate: `source_path.exists()` and is within `runbook_dir`
  - Determine if it's a file or directory
  - Copy to temp directory:
    - **Files**: `shutil.copy2(source_path, temp_exec_dir / source_path.name)`
    - **Directories**: `shutil.copytree(source_path, temp_exec_dir / source_path.name, dirs_exist_ok=True)`
  - Preserve relative structure if needed (or flatten to temp_exec_dir root)
- Handle errors gracefully (log warnings, collect error messages)
- Return list of errors (empty list if all copies succeeded)

**Files to modify:**
- `src/services/script_executor.py`

### 2.2 Update ScriptExecutor.execute_script Signature

**Add parameters to `execute_script` method:**
- `input_paths: Optional[List[str]] = None` - List of input file/folder paths
- `runbook_dir: Optional[Path] = None` - Path to runbook directory (for resolving input paths)

**Update method to:**
- Call `_copy_input_files` after creating `temp_exec_dir` but before executing script
- Only copy if `input_paths` and `runbook_dir` are provided
- Handle errors from `_copy_input_files` appropriately (log and continue, or fail-fast)

**Files to modify:**
- `src/services/script_executor.py` (method `execute_script`)

### 2.3 Update RunbookService.execute_runbook

**Extract input paths and pass to ScriptExecutor:**
- After loading runbook content, extract File System Requirements
- Get Input list using `RunbookParser.extract_file_requirements`
- Pass `input_paths` and `runbook_path.parent` to `ScriptExecutor.execute_script`

**Example flow:**
```python
# In execute_runbook method, after extracting script:
fs_section = RunbookParser.extract_section(content, 'File System Requirements')
if fs_section:
    requirements = RunbookParser.extract_file_requirements(fs_section)
    input_paths = requirements.get('Input', [])
else:
    input_paths = []

# When calling ScriptExecutor.execute_script:
return_code, stdout, stderr = ScriptExecutor.execute_script(
    script,
    env_vars,
    token_string=token_string,
    correlation_id=correlation_id,
    recursion_stack=new_recursion_stack,
    input_paths=input_paths,
    runbook_dir=runbook_path.parent
)
```

**Files to modify:**
- `src/services/runbook_service.py` (method `execute_runbook`)

---

## Phase 3: Security Verification and Testing

### 3.1 Verify Thread Safety

**Current implementation analysis:**
- `tempfile.mkdtemp()` is thread-safe (uses OS-level atomic operations)
- Each execution gets a unique directory via UUID prefix: `f'runbook-exec-{uuid.uuid4().hex[:8]}-'`
- No shared state between concurrent executions
- Each execution has its own `temp_exec_dir` variable

**Verification:**
- Review `tempfile.mkdtemp()` documentation (Python standard library, thread-safe)
- Verify UUID generation is safe for concurrent use (`uuid.uuid4()` is thread-safe)
- Consider adding a comment documenting thread safety

**Action:**
- Add documentation comment if needed
- No code changes required (implementation is already thread-safe)

### 3.2 Verify Path Isolation

**Current implementation analysis:**
- Script execution uses `cwd=str(temp_exec_dir)` parameter in `subprocess.run()`
- This restricts the script's working directory to `temp_exec_dir`
- Scripts cannot access paths outside `temp_exec_dir` using relative paths
- Absolute paths like `/` or `/etc` are not accessible (OS-level restriction in container)

**Verification steps:**
1. Verify `cwd` parameter is set correctly (already done: line 232 in `script_executor.py`)
2. Test that scripts cannot access parent directories using `../`
3. Test that scripts cannot access absolute paths (if running in container, these are naturally restricted)
4. Add input path validation to prevent directory traversal in `_copy_input_files`

**Actions:**
- Add comprehensive path validation in `_copy_input_files` (see Phase 2.1)
- Add tests to verify path isolation (see Phase 4.2)

### 3.3 Verify Cleanup

**Current implementation analysis:**
- Cleanup uses `shutil.rmtree(temp_exec_dir)` in a `finally` block (line 298)
- `shutil.rmtree()` recursively removes directory and all contents
- Cleanup happens even if execution fails (finally block ensures execution)
- Error handling logs warnings if cleanup fails but doesn't raise

**Verification:**
- Review `shutil.rmtree()` documentation (recursively removes directory tree)
- Verify cleanup happens in finally block (already correct)
- Verify error handling doesn't mask execution errors

**Action:**
- No changes needed (implementation is correct)
- Consider adding a test to verify cleanup on error (may already exist)

---

## Phase 4: Testing

### 4.1 Update Existing Tests

**Remove Output-related tests:**
- Update all test runbooks to remove Output sections
- Remove assertions checking Output parsing
- Remove Output validation tests

### 4.2 Add New Tests for Input Copying

**Test file: `test/unit/services/test_script_executor.py`**

**New tests to add:**

1. **`test_copy_input_files_single_file`**
   - Copy a single file to temp directory
   - Verify file exists in temp directory
   - Verify file contents match

2. **`test_copy_input_files_multiple_files`**
   - Copy multiple files to temp directory
   - Verify all files exist

3. **`test_copy_input_files_directory`**
   - Copy a directory to temp directory
   - Verify directory structure is preserved
   - Verify all files in directory are copied

4. **`test_copy_input_files_mixed_files_and_directories`**
   - Copy mix of files and directories
   - Verify all are copied correctly

5. **`test_copy_input_files_path_traversal_prevention`**
   - Test that `../` paths are rejected
   - Test that absolute paths outside runbook_dir are rejected
   - Test that paths escaping runbook_dir are rejected

6. **`test_copy_input_files_nonexistent_file`**
   - Test handling of non-existent input files
   - Should log error and return error message
   - Execution should continue (or fail-fast based on design decision)

7. **`test_execute_script_with_input_files`**
   - Execute a script that uses input files
   - Verify script can access files using `./filename`
   - Verify script execution succeeds

8. **`test_execute_script_input_files_in_working_directory`**
   - Verify input files are accessible in script's working directory
   - Script should be able to use `./file` or `file` to access inputs

### 4.3 Add Integration Tests

**Test file: `test/integration/test_integration.py`**

**New tests:**
- End-to-end test executing a runbook with input files
- Verify files are copied and accessible to script
- Verify script execution succeeds

### 4.4 Update E2E Tests

**Test file: `test/e2e/test_e2e.py`**

**If applicable:**
- Update e2e tests to include input file scenarios
- Or create new e2e tests for input file functionality

---

## Phase 5: Documentation Updates

### 5.1 Update RUNBOOK.md

**Changes:**
1. Remove Output from File System Requirements section
2. Update section description to focus on Input only
3. Add documentation about Input files/folders being copied to execution directory
4. Update Execution Processing section to mention input file copying
5. Add examples showing Input with files and directories

**Example updated section:**

# File System Requirements
This section must contain information about what files and folders should be in place for the script to run. The file naming convention RunbookName.someType if there is only one or two files. If there are many files, you can create a folder with the RunbookName and store the files there. Input files and folders are copied to the temporary execution directory before script execution, making them available to the script using relative paths like `./file` or `./folder/file`.

```yaml
Input:
- ./Runbook.dockerfile
- ./Runbook/one_of_many_files.csv
- ./data/input_folder
```


### 5.2 Update README.md

**If README mentions Output:**
- Remove Output references
- Update examples to show Input only

### 5.3 Update API Documentation

**If OpenAPI spec mentions Output:**
- Remove Output from any schema definitions
- Update examples

---

## Implementation Order

1. **Phase 1**: Remove Output support (cleanup, no new functionality)
2. **Phase 2**: Implement Input copying (core functionality)
3. **Phase 3**: Security verification (review and document)
4. **Phase 4**: Testing (ensure everything works)
5. **Phase 5**: Documentation (update docs to match implementation)

---

## Security Considerations

### Input Path Validation

**Critical: Prevent directory traversal attacks**

When copying input files, validate paths to prevent:
- `../` components escaping runbook directory
- Absolute paths accessing files outside runbook directory
- Symlink attacks (consider resolving symlinks)

**Validation strategy:**
1. Resolve path relative to `runbook_dir`: `source_path = (runbook_dir / input_path).resolve()`
2. Verify `source_path` is within `runbook_dir`:
   - Python 3.9+: Use `source_path.is_relative_to(runbook_dir.resolve())`
   - Python 3.8: Compare `source_path` and `runbook_dir.resolve()` using `parts` or check if `runbook_dir.resolve()` is a parent
3. Reject if validation fails (log error, return error message)

### Execution Isolation

**Current protections:**
- Script executes with `cwd=temp_exec_dir` (working directory restriction)
- Container isolation (if running in Docker) provides additional security
- Script cannot access files outside temp directory using relative paths

**Recommendations:**
- Document that scripts run in isolated directory
- Consider additional restrictions if needed (chroot, namespaces) - but current implementation is sufficient for most use cases

---

## Backward Compatibility

**Breaking changes:**
- Output section is removed (no backward compatibility needed per requirements)
- Runbooks with Output sections will fail validation after this refactor
- Runbooks must be updated to remove Output sections

**Migration path:**
- None required (explicit requirement: no backward compatibility)
- Sample runbooks will be updated as part of this refactor

---

## Risk Assessment

**Low Risk:**
- Removing Output section (straightforward deletion)
- Thread safety (already implemented correctly)
- Cleanup (already implemented correctly)

**Medium Risk:**
- Input file copying (new functionality, needs thorough testing)
- Path validation (security-critical, needs careful implementation)

**Mitigation:**
- Comprehensive testing (unit, integration, e2e)
- Careful path validation implementation
- Security review of path validation logic

---

## Success Criteria

1. ✅ Output section completely removed from codebase
2. ✅ Input files/folders are copied to temporary execution directory
3. ✅ Scripts can access input files using `./file` or `file`
4. ✅ Path validation prevents directory traversal attacks
5. ✅ Thread safety verified and documented
6. ✅ Execution isolation verified (scripts cannot access `/` or `../something`)
7. ✅ Cleanup verified (directory and all sub-folders removed)
8. ✅ All tests pass
9. ✅ Documentation updated
10. ✅ Sample runbooks updated

---

## Notes

- This refactor does not require backward compatibility
- Input paths are resolved relative to the runbook's directory
- Files are copied (not symlinked) for security and isolation
- Directory structure in temp folder: All inputs copied to root of `temp_exec_dir` (flattened structure)
  - Alternative: Preserve relative structure (e.g., `temp_exec_dir/input_path`)
  - Decision needed: Flatten vs. preserve structure (recommend flattening for simplicity)
- Consider whether to fail-fast if input file copy fails, or log warnings and continue
  - Recommendation: Fail-fast (return error, don't execute script) for clarity
