# Refactor Plan: Script Access to Token and Tracking Breadcrumb

## Implementation Status

- [x] Phase 1: Configuration Updates
- [x] Phase 2: Script Executor Updates
- [x] Phase 3: Breadcrumb Updates
- [ ] Phase 4: Runbook Service Updates
- [ ] Phase 5: Route Updates
- [ ] Phase 6: Documentation Updates
- [ ] Phase 7: Test Updates

## Overview

This refactor enables runbooks to call the Runbook API to execute sub-runbooks by providing scripts with:
1. **JWT Token** - For authenticating API requests
2. **Correlation ID** - For tracking request chains across nested runbook executions
3. **Recursion Protection** - To prevent infinite loops and cycles

## Goals

- Allow runbooks to execute sub-runbooks via API calls
- Maintain request correlation across nested executions
- Prevent infinite recursion and circular dependencies
- Preserve security and isolation of script execution
- Document usage patterns and safety mechanisms

## Design Decisions

### Environment Variables for Scripts

Scripts will receive the following environment variables automatically:

1. **`RUNBOOK_API_TOKEN`** - The JWT token string (from Authorization header)
   - Used for authenticating API requests
   - Should be passed in `Authorization: Bearer $RUNBOOK_API_TOKEN` header

2. **`RUNBOOK_CORRELATION_ID`** - The correlation ID from the breadcrumb
   - Used for request tracing across nested executions
   - Should be passed in `X-Correlation-Id: $RUNBOOK_CORRELATION_ID` header

3. **`RUNBOOK_API_BASE_URL`** - The base URL for the API (e.g., `http://localhost:8083`)
   - Constructed from `API_PROTOCOL` (default: `http`), `API_HOST` (default: `localhost`), and `API_PORT` (default: `8083`) config values
   - Format: `{API_PROTOCOL}://{API_HOST}:{API_PORT}`
   - Allows scripts to make API calls
   - Scripts run in the same container, so `localhost` is appropriate for most cases

4. **`RUNBOOK_RECURSION_STACK`** - JSON array of runbook filenames in the execution chain
   - Format: `["ParentRunbook.md"]` (includes current runbook)
   - Used to detect recursion and cycles
   - **Automatically includes the current runbook's filename** before being passed to the script
   - Scripts simply pass this value as-is in the `X-Recursion-Stack` header when calling sub-runbooks
   - For top-level executions, this will be `["CurrentRunbook.md"]` (not empty - includes the current runbook)

### Recursion Protection

**Recursion Detection:**
- Before executing a runbook, check if its filename appears in the recursion stack from breadcrumb
- If found, reject execution and write meaningful error to stderr: "Recursion detected: Runbook {filename} already in execution chain: {stack}"
- This prevents both infinite loops and circular dependencies
- Error is written to stderr so it persists in execution history

**Recursion Depth Limit:**
- Provides defense-in-depth against very deep legitimate nesting that could exhaust resources
- Check recursion stack length against `MAX_RECURSION_DEPTH` config value
- If limit exceeded, reject execution and write error to stderr: "Recursion depth limit exceeded: {current_depth} (max: {MAX_RECURSION_DEPTH})"
- Default: 50 (high value to allow legitimate deep nesting while preventing abuse)

**Stack Management:**
- **Breadcrumb responsibility**: Recursion stack is stored in the breadcrumb dictionary
- **Before passing to script**: The system automatically adds the current runbook's filename to the recursion stack in breadcrumb
- The stack passed to the script already includes the current runbook: `["CurrentRunbook.md"]`
- Scripts pass the stack as-is to sub-runbook API calls (no manipulation needed)
- The API will check if the sub-runbook is already in the stack before executing
- If not in stack, API adds sub-runbook and continues: `["CurrentRunbook.md", "SubRunbook.md"]`

**Runtime Safety:**
- If a script calls a sub-runbook without passing `X-Recursion-Stack` header:
  - API treats it as a new top-level execution (recursion_stack = None)
  - This allows scripts to "break out" of recursion tracking if needed
  - However, this means recursion protection is lost for that sub-call
  - **Recommendation**: Document that scripts should always pass the recursion stack
  - **Future enhancement**: Could add a config flag to require recursion stack header

## Implementation Plan

### Phase 1: Configuration Updates

**File: `src/config/config.py`**
- Add `API_PROTOCOL` configuration (default: `http`) - for constructing API base URL
- Add `API_HOST` configuration (default: `localhost`) - scripts run in same container, so localhost is appropriate
- Use existing `API_PORT` configuration (default: `8083`)
- Add `MAX_RECURSION_DEPTH` configuration (default: 50, high value to allow legitimate nesting)
- Construct `RUNBOOK_API_BASE_URL` as `{API_PROTOCOL}://{API_HOST}:{API_PORT}` in ScriptExecutor
- Update `config_items` tracking to include new configs

### Phase 2: Script Executor Updates

**File: `src/services/script_executor.py`**

1. **Update `execute_script` signature:**
   ```python
   def execute_script(
       script: str, 
       env_vars: Optional[Dict[str, str]] = None,
       token_string: Optional[str] = None,
       correlation_id: Optional[str] = None,
       recursion_stack: Optional[List[str]] = None
   ) -> Tuple[int, str, str]:
   ```

2. **Add automatic environment variables:**
   - Extract JWT token string from request (need to pass from route)
   - Set `RUNBOOK_API_TOKEN` if token_string provided
   - Set `RUNBOOK_CORRELATION_ID` if correlation_id provided
   - Construct and set `RUNBOOK_API_BASE_URL` as `{config.API_PROTOCOL}://{config.API_HOST}:{config.API_PORT}`
   - Set `RUNBOOK_RECURSION_STACK` as JSON string from recursion_stack (from breadcrumb)
   - **Note**: The recursion_stack passed here should already include the current runbook's filename

3. **Validation:**
   - These variables are system-managed and should not be overridden by user env_vars
   - Log warning if user tries to set them (but don't fail - just ignore user value)

### Phase 3: Breadcrumb Updates

**File: `src/flask_utils/breadcrumb.py`**

1. **Update `create_flask_breadcrumb` function:**
   - Extract recursion_stack from `X-Recursion-Stack` header if present (parse JSON)
   - If header is invalid/missing, set recursion_stack to None (top-level execution)
   - Add `recursion_stack` to breadcrumb dictionary (defaults to None if not provided)
   - **Default empty recursion stack comes from breadcrumb constructor** - not from service layer

2. **Breadcrumb structure:**
   ```python
   {
       "at_time": datetime,
       "by_user": str,
       "from_ip": str,
       "correlation_id": str,
       "recursion_stack": Optional[List[str]]  # New field
   }
   ```

### Phase 4: Runbook Service Updates

**File: `src/services/runbook_service.py`**

1. **Update `execute_runbook` method:**
   - Extract recursion_stack from breadcrumb (breadcrumb.get('recursion_stack'))
   - **Default empty recursion stack comes from breadcrumb constructor** (None for top-level)
   - If recursion_stack is None, treat as top-level execution (empty list for building new stack)

2. **Add recursion validation (before execution):**
   - **Primary check**: Check if filename is already in recursion_stack
   - If found, return error with meaningful message to stderr:
     - `return_code = 1`
     - `stdout = ""`
     - `stderr = f"Recursion detected: Runbook {filename} already in execution chain: {recursion_stack}"`
   - This error will be persisted in execution history
   
   - **Secondary check**: Check recursion_stack length against MAX_RECURSION_DEPTH
   - If limit exceeded, return error to stderr:
     - `return_code = 1`
     - `stdout = ""`
     - `stderr = f"Recursion depth limit exceeded: {len(recursion_stack)} (max: {config.MAX_RECURSION_DEPTH})"`
   - Log recursion attempts for security monitoring

3. **Build recursion stack for script (includes current runbook):**
   - Create new_stack = (recursion_stack or []) + [filename]
   - **This new_stack includes the current runbook's filename**
   - Update breadcrumb with new_stack: `breadcrumb['recursion_stack'] = new_stack`
   - Pass updated breadcrumb, token_string, and correlation_id to ScriptExecutor
   - ScriptExecutor will extract recursion_stack from breadcrumb and set `RUNBOOK_RECURSION_STACK` env var
   - Scripts receive the stack with current runbook already included, and pass it as-is to sub-runbook calls

### Phase 5: Route Updates

**File: `src/routes/runbook_routes.py`**

1. **Update `execute_runbook` route:**
   - Extract raw JWT token string from Authorization header
   - Create breadcrumb using `create_flask_breadcrumb(token)` - this will extract recursion_stack from `X-Recursion-Stack` header
   - Pass token_string and breadcrumb to runbook_service.execute_runbook
   - Service will extract recursion_stack from breadcrumb and handle recursion validation

2. **Token extraction:**
   - Get `Authorization` header value
   - Extract token after "Bearer " prefix
   - Pass to service layer

3. **Recursion stack handling:**
   - Breadcrumb creation handles `X-Recursion-Stack` header parsing
   - If header is missing or invalid, recursion_stack is None (top-level execution)
   - This provides runtime safety: scripts that don't pass the header will start a new execution chain

### Phase 6: Documentation Updates

**File: `RUNBOOK.md`**

Add new section: **"Sub-Runbook Execution"**

Document:
- How to call sub-runbooks from scripts
- Available environment variables
- Recursion protection mechanisms
- Example script calling another runbook
- Best practices and safety considerations

**File: `README.md`**

Update:
- Mention sub-runbook execution capability
- Reference new RUNBOOK.md section
- Note recursion limits and safety features

**File: `samples/runbooks/`**

Create example runbook:
- `ParentRunbook.md` - Calls the existing `SimpleRunbook.md` as a child runbook
- Demonstrates proper usage: passing token, correlation ID, and recursion stack
- Shows how to handle sub-runbook responses
- Uses existing `SimpleRunbook.md` as the child (no need to create new child runbook)

### Phase 7: Test Updates

**Unit Tests:**

1. **`test/unit/services/test_script_executor.py`**
   - Test that system env vars are set correctly
   - Test that user cannot override system vars
   - Test recursion_stack JSON encoding (should include current runbook)
   - Test token and correlation_id passing
   - Test that recursion_stack passed to script includes current runbook filename

2. **`test/unit/services/test_runbook_service.py`**
   - Test recursion detection (same runbook in stack)
   - Test recursion errors written to stderr (for history persistence)
   - Test recursion depth limit enforcement
   - Test stack building (appending current filename before passing to script)
   - Test that stack passed to script includes current runbook
   - Test error handling for recursion violations
   - Test missing recursion_stack header (runtime safety - should start new chain)

3. **`test/unit/flask_utils/test_breadcrumb.py`**
   - Test recursion_stack extraction from X-Recursion-Stack header
   - Test recursion_stack parsing (JSON array)
   - Test invalid/missing header handling (should be None)
   - Test breadcrumb structure with recursion_stack

4. **`test/unit/routes/test_runbook_routes.py`** (if exists)
   - Test token extraction from Authorization header
   - Test passing token and breadcrumb to service layer

**Integration Tests:**

1. **`test/integration/test_integration.py`**
   - Test nested runbook execution (parent -> child)
   - Test recursion detection
   - Test correlation ID propagation

**E2E Tests:**

1. **`test/e2e/test_e2e.py`**
   - Test complete workflow: parent runbook calls child runbook
   - Test recursion protection (attempt to call self)
   - Test correlation ID in logs/history
   - Test deep nesting (up to limit)
   - Test recursion limit enforcement

## Security Considerations

1. **Token Exposure:**
   - JWT token is passed as environment variable (visible in process list)
   - This is acceptable as scripts run in isolated temp directories
   - Token is only valid for the execution duration
   - Consider token expiration handling in scripts

2. **Recursion Protection:**
   - Prevents infinite loops and resource exhaustion
   - Limits maximum nesting depth
   - Logs all recursion attempts for monitoring

3. **Environment Variable Validation:**
   - System variables are protected from user override
   - User variables still validated for name format
   - System variables are logged (token value masked)

4. **API Base URL:**
   - Constructed from API_PROTOCOL, API_HOST, and API_PORT config values
   - Default: `http://localhost:8083` (scripts run in same container)
   - Can be configured for different deployment scenarios (e.g., https behind proxy)

5. **Runtime Safety:**
   - If scripts don't pass `X-Recursion-Stack` header, execution proceeds as top-level
   - This allows scripts to "break out" of recursion tracking if needed
   - However, recursion protection is lost for that sub-call
   - Documented as best practice to always pass the header
   - Future: Could add config flag to require recursion stack header

## Example Usage

### Parent Runbook Script

```sh
#! /bin/zsh
echo "Parent runbook starting"
echo "Correlation ID: $RUNBOOK_CORRELATION_ID"
echo "Recursion stack: $RUNBOOK_RECURSION_STACK"

# Call child runbook via API
# The recursion stack already includes this runbook's filename
# Just pass it as-is in the X-Recursion-Stack header
RESPONSE=$(curl -s -X POST "$RUNBOOK_API_BASE_URL/api/runbooks/ChildRunbook.md/execute" \
  -H "Authorization: Bearer $RUNBOOK_API_TOKEN" \
  -H "X-Correlation-Id: $RUNBOOK_CORRELATION_ID" \
  -H "X-Recursion-Stack: $RUNBOOK_RECURSION_STACK" \
  -H "Content-Type: application/json" \
  -d '{"env_vars":{"CHILD_VAR":"value"}}')

echo "Child runbook response: $RESPONSE"
echo "Parent runbook completed"
```

**Note:** The recursion stack passed to scripts already includes the current runbook's filename (e.g., `["ParentRunbook.md"]`). Scripts simply pass this value as-is in the `X-Recursion-Stack` header. The API will check if the child runbook is already in the stack before executing, preventing recursion.

### Recursion Protection Example

If a runbook tries to call itself (or a runbook already in its chain):

```sh
#! /bin/zsh
# This will fail with recursion error
# The recursion stack already contains this runbook's name: ["ParentRunbook.md"]
# When we try to call ParentRunbook.md again, the API detects it's already in the stack
curl -X POST "$RUNBOOK_API_BASE_URL/api/runbooks/ParentRunbook.md/execute" \
  -H "Authorization: Bearer $RUNBOOK_API_TOKEN" \
  -H "X-Correlation-Id: $RUNBOOK_CORRELATION_ID" \
  -H "X-Recursion-Stack: $RUNBOOK_RECURSION_STACK" \
  -H "Content-Type: application/json" \
  -d '{"env_vars":{}}'
# Error: Recursion detected: ParentRunbook.md already in execution chain
```

**How it works:**
1. Script receives `RUNBOOK_RECURSION_STACK=["ParentRunbook.md"]` (includes current runbook)
2. Script passes this stack to API call for `ParentRunbook.md`
3. API checks: Is `ParentRunbook.md` in the stack? Yes!
4. API rejects with 400 Bad Request error before execution

## Migration Notes

- Existing runbooks continue to work without changes
- New environment variables are optional (only set if token/correlation_id provided)
- No breaking changes to API contracts
- Backward compatible with existing scripts

## Testing Checklist

- [ ] System env vars set correctly in scripts
- [ ] User cannot override system vars
- [ ] Recursion stack stored in breadcrumb (centralized responsibility)
- [ ] Recursion stack includes current runbook filename before passing to script
- [ ] Scripts can pass recursion stack as-is (no manipulation needed)
- [ ] Recursion detection works (same runbook in chain)
- [ ] Recursion errors written to stderr (persist in history)
- [ ] API base URL constructed from API_PROTOCOL, API_HOST, and API_PORT
- [ ] MAX_RECURSION_DEPTH config added and enforced
- [ ] Runtime safety: Missing recursion stack header handled gracefully
- [ ] Correlation ID propagated correctly
- [ ] Token passed correctly to scripts
- [ ] API base URL configurable
- [ ] Example runbooks work correctly
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Documentation updated
- [ ] Security considerations addressed

## Future Enhancements (Out of Scope)

- Token refresh mechanism for long-running scripts
- Recursion stack visualization in UI
- Metrics for recursion depth distribution
- Support for parallel sub-runbook execution (with shared recursion stack)
