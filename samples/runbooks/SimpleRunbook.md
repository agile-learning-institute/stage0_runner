# SimpleRunbook
This is a simple test runbook that demonstrates the basic functionality of the stage0_runner utility. It performs a simple echo operation and lists the current directory.

# Environment Requirements
```yaml
TEST_VAR: A test environment variable for demonstration purposes
```

# File System Requirements
```yaml
Input:
Output:
```

# Required Claims
```yaml
roles: developer, admin
```
This section is optional. If present, the token must include the specified claims to execute or validate the runbook.
- `roles`: List of roles (comma-separated) that are allowed to execute/validate this runbook
- Other claims can be specified as key-value pairs where the value is a comma-separated list of allowed values

# Script
```sh
#! /bin/zsh
echo "Running SimpleRunbook"
echo "Test variable value: ${TEST_VAR:-not set}"
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la
echo "SimpleRunbook completed successfully"
```

# History


### 2026-01-14T18:58:12.497Z | Exit Code: 1

**Stderr:**
```
Validation error
```

### 2026-01-14T18:58:12.503Z | Exit Code: 1

**Stderr:**
```
Recursion detected: Runbook SimpleRunbook.md already in execution chain: ['ParentRunbook.md', 'SimpleRunbook.md']
```

### 2026-01-14T18:58:12.504Z | Exit Code: 1

**Stderr:**
```
Recursion depth limit exceeded: 50 (max: 50)
```

### 2026-01-14T18:58:12.504Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:58:12.505Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:58:12.506Z | Exit Code: 0

**Stdout:**
```
success
```

