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


## 2026-01-08t23:03:00.372
- Completed: 2026-01-08t23:03:00.384
- Return Code: 0

### stdout
```
Running SimpleRunbook
Test variable value: testvalue
Current directory: /workspace
Listing files:
total 24
drwxr-xr-x 7 root root  224 Jan  8 23:03 .
drwxr-xr-x 1 root root 4096 Jan  8 23:02 ..
-rw-r--r-- 1 root root  122 Jan  7 22:12 CreatePackage.dockerfile
-rw-r--r-- 1 root root  949 Jan  8 18:55 CreatePackage.md
-rw-r--r-- 1 root root  646 Jan  8 18:55 Runbook.md
-rw-r--r-- 1 root root  969 Jan  8 22:03 SimpleRunbook.md
-rwxr-xr-x 1 root root  195 Jan  8 23:03 temp.zsh
SimpleRunbook completed successfully

```

### stderr
```

```

## 2026-01-08t23:11:49.644
- Completed: 2026-01-08t23:11:49.650
- Return Code: 0

### stdout
```
Running SimpleRunbook
Test variable value: foo
Current directory: /workspace
Listing files:
total 24
drwxr-xr-x 7 root root  224 Jan  8 23:11 .
drwxr-xr-x 1 root root 4096 Jan  8 23:02 ..
-rw-r--r-- 1 root root  122 Jan  7 22:12 CreatePackage.dockerfile
-rw-r--r-- 1 root root  949 Jan  8 18:55 CreatePackage.md
-rw-r--r-- 1 root root  646 Jan  8 18:55 Runbook.md
-rw-r--r-- 1 root root 1608 Jan  8 23:03 SimpleRunbook.md
-rwxr-xr-x 1 root root  195 Jan  8 23:11 temp.zsh
SimpleRunbook completed successfully

```

### stderr
```

```
