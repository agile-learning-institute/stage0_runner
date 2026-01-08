# Test Coverage Analysis

## Current Test Structure

The test directory has a **flat structure** with 3 test files:

```
test/
├── test_e2e.py          # End-to-end tests (10 tests)
├── test_integration.py  # Integration tests (33 tests)
└── test_runbook_service.py  # Unit tests (52 tests)
```

**Total: ~95 tests**

## Source Code Structure

```
src/
├── config/
│   └── config.py
├── flask_utils/
│   ├── breadcrumb.py
│   ├── exceptions.py
│   ├── route_wrapper.py
│   └── token.py
├── routes/
│   ├── config_routes.py
│   ├── dev_login_routes.py
│   ├── explorer_routes.py
│   ├── runbook_routes.py
│   └── shutdown_routes.py
├── services/
│   ├── history_manager.py
│   ├── rbac_authorizer.py
│   ├── runbook_parser.py
│   ├── runbook_service.py
│   ├── runbook_validator.py
│   └── script_executor.py
└── server.py
```

## Test Coverage by Module

### ✅ Well Tested (via integration/e2e tests)

1. **`src/services/runbook_service.py`** - ✅ Well tested
   - Unit tests in `test_runbook_service.py`
   - Integration tests in `test_integration.py`
   - E2E tests in `test_e2e.py`

2. **`src/services/runbook_parser.py`** - ✅ Well tested
   - Tested via `test_runbook_service.py` (many tests for parsing)

3. **`src/services/runbook_validator.py`** - ✅ Well tested
   - Tested via `test_runbook_service.py`

4. **`src/services/script_executor.py`** - ✅ Well tested
   - Tested via `test_runbook_service.py` (timeout, output limits, env vars)

5. **`src/services/rbac_authorizer.py`** - ✅ Well tested
   - Tested via `test_runbook_service.py` (multiple RBAC scenarios)
   - Integration tests verify RBAC enforcement

6. **`src/routes/runbook_routes.py`** - ✅ Well tested
   - Integration tests cover all endpoints
   - E2E tests verify complete workflows

7. **`src/routes/dev_login_routes.py`** - ✅ Well tested
   - Integration tests cover dev-login endpoint

8. **`src/routes/config_routes.py`** - ✅ Well tested
   - Integration tests cover config endpoint

9. **`src/server.py`** - ✅ Well tested
   - Tested via integration/e2e tests (app creation)

### ⚠️ Partially Tested (indirectly via integration tests)

10. **`src/services/history_manager.py`** - ⚠️ Indirectly tested
    - Tested via integration/e2e tests (history is appended)
    - **Missing**: Direct unit tests for history parsing, formatting, edge cases

11. **`src/flask_utils/token.py`** - ⚠️ Indirectly tested
    - Tested via integration tests (token creation/validation)
    - **Missing**: Direct unit tests for Token class, edge cases, error handling

12. **`src/flask_utils/route_wrapper.py`** - ⚠️ Indirectly tested
    - Tested via integration tests (exception handling)
    - **Missing**: Direct unit tests for exception decorator, all exception types

13. **`src/flask_utils/breadcrumb.py`** - ⚠️ Indirectly tested
    - Tested via integration tests (breadcrumb creation)
    - **Missing**: Direct unit tests

14. **`src/flask_utils/exceptions.py`** - ⚠️ Indirectly tested
    - Tested via integration tests (exception raising)
    - **Missing**: Direct unit tests for exception classes

15. **`src/routes/explorer_routes.py`** - ⚠️ Partially tested
    - Integration test verifies endpoint is public
    - **Missing**: Tests for file serving, error cases

16. **`src/routes/shutdown_routes.py`** - ⚠️ Partially tested
    - Integration test verifies endpoint requires auth
    - **Missing**: Tests for actual shutdown behavior, Gunicorn vs Flask dev server

### ❌ Not Directly Tested

17. **`src/config/config.py`** - ❌ No direct unit tests
    - Tested indirectly via integration tests
    - **Missing**: Unit tests for Config singleton, defaults, environment variable parsing

## Why No Mirrored Test Structure?

The current flat structure exists because:

1. **Historical Development**: Tests were written as the codebase evolved, not following a strict structure
2. **Functional Testing Approach**: Tests are organized by **test type** (unit/integration/e2e) rather than by **module**
3. **Service-Centric**: Most tests focus on `RunbookService` which orchestrates other modules
4. **Integration-First**: Heavy emphasis on integration tests that test multiple modules together

## Recommended Test Structure

A mirrored structure would look like:

```
test/
├── unit/
│   ├── config/
│   │   └── test_config.py
│   ├── flask_utils/
│   │   ├── test_breadcrumb.py
│   │   ├── test_exceptions.py
│   │   ├── test_route_wrapper.py
│   │   └── test_token.py
│   ├── routes/
│   │   ├── test_config_routes.py
│   │   ├── test_dev_login_routes.py
│   │   ├── test_explorer_routes.py
│   │   ├── test_runbook_routes.py
│   │   └── test_shutdown_routes.py
│   └── services/
│       ├── test_history_manager.py
│       ├── test_rbac_authorizer.py
│       ├── test_runbook_parser.py
│       ├── test_runbook_service.py  # Keep existing
│       ├── test_runbook_validator.py
│       └── test_script_executor.py
├── integration/
│   └── test_integration.py  # Keep existing
└── e2e/
    └── test_e2e.py  # Keep existing
```

## Benefits of Mirrored Structure

1. **Discoverability**: Easy to find tests for a specific module
2. **Organization**: Clear separation of unit vs integration vs e2e
3. **Maintainability**: When a module changes, tests are easy to locate
4. **Coverage Visibility**: Easier to see what's missing
5. **Scalability**: As codebase grows, structure remains clear

## Coverage Gaps to Address

### High Priority
1. **`src/config/config.py`** - Core configuration logic needs unit tests
2. **`src/services/history_manager.py`** - History parsing/formatting edge cases
3. **`src/flask_utils/token.py`** - Token validation edge cases

### Medium Priority
4. **`src/flask_utils/route_wrapper.py`** - Exception handling decorator
5. **`src/routes/shutdown_routes.py`** - Shutdown behavior
6. **`src/routes/explorer_routes.py`** - File serving edge cases

### Low Priority
7. **`src/flask_utils/breadcrumb.py`** - Simple utility, well tested indirectly
8. **`src/flask_utils/exceptions.py`** - Simple exception classes

## Estimated Coverage

Based on analysis:
- **Services**: ~85% coverage (good)
- **Routes**: ~75% coverage (good via integration)
- **Flask Utils**: ~60% coverage (needs improvement)
- **Config**: ~40% coverage (needs improvement)

**Overall Estimated Coverage: ~70-75%**

Note: Actual coverage can only be determined by running `pytest --cov` with all dependencies installed.

