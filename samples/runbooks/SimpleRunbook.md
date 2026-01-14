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

### 2026-01-14T18:34:51.791Z | Exit Code: 1

**Stderr:**
```
Validation error
```

### 2026-01-14T18:34:51.795Z | Exit Code: 1

**Stderr:**
```
Recursion detected: Runbook SimpleRunbook.md already in execution chain: ['ParentRunbook.md', 'SimpleRunbook.md']
```

### 2026-01-14T18:34:51.796Z | Exit Code: 1

**Stderr:**
```
Recursion depth limit exceeded: 50 (max: 50)
```

### 2026-01-14T18:34:51.797Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:34:51.797Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:34:51.798Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:35:05.682Z | Exit Code: 1

**Stderr:**
```
Validation error
```

### 2026-01-14T18:35:05.686Z | Exit Code: 1

**Stderr:**
```
Recursion detected: Runbook SimpleRunbook.md already in execution chain: ['ParentRunbook.md', 'SimpleRunbook.md']
```

### 2026-01-14T18:35:05.687Z | Exit Code: 1

**Stderr:**
```
Recursion depth limit exceeded: 50 (max: 50)
```

### 2026-01-14T18:35:05.687Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:35:05.688Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:35:05.689Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:35:11.062Z | Exit Code: 1

**Stderr:**
```
Validation error
```

### 2026-01-14T18:35:11.066Z | Exit Code: 1

**Stderr:**
```
Recursion detected: Runbook SimpleRunbook.md already in execution chain: ['ParentRunbook.md', 'SimpleRunbook.md']
```

### 2026-01-14T18:35:11.066Z | Exit Code: 1

**Stderr:**
```
Recursion depth limit exceeded: 50 (max: 50)
```

### 2026-01-14T18:35:11.067Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:35:11.068Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:35:11.069Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:41:25.779Z | Exit Code: 1

**Stderr:**
```
Validation error
```

### 2026-01-14T18:41:25.783Z | Exit Code: 1

**Stderr:**
```
Recursion detected: Runbook SimpleRunbook.md already in execution chain: ['ParentRunbook.md', 'SimpleRunbook.md']
```

### 2026-01-14T18:41:25.783Z | Exit Code: 1

**Stderr:**
```
Recursion depth limit exceeded: 50 (max: 50)
```

### 2026-01-14T18:41:25.784Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:41:25.785Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:41:25.785Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:41:59.333Z | Exit Code: 1

**Stderr:**
```
Validation error
```

### 2026-01-14T18:41:59.338Z | Exit Code: 1

**Stderr:**
```
Recursion detected: Runbook SimpleRunbook.md already in execution chain: ['ParentRunbook.md', 'SimpleRunbook.md']
```

### 2026-01-14T18:41:59.338Z | Exit Code: 1

**Stderr:**
```
Recursion depth limit exceeded: 50 (max: 50)
```

### 2026-01-14T18:41:59.339Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:41:59.340Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:41:59.340Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:42:23.729Z | Exit Code: 1

**Stderr:**
```
Validation error
```

### 2026-01-14T18:42:23.733Z | Exit Code: 1

**Stderr:**
```
Recursion detected: Runbook SimpleRunbook.md already in execution chain: ['ParentRunbook.md', 'SimpleRunbook.md']
```

### 2026-01-14T18:42:23.734Z | Exit Code: 1

**Stderr:**
```
Recursion depth limit exceeded: 50 (max: 50)
```

### 2026-01-14T18:42:23.735Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:42:23.736Z | Exit Code: 0

**Stdout:**
```
success
```


### 2026-01-14T18:42:23.736Z | Exit Code: 0

**Stdout:**
```
success
```

