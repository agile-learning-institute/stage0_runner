# SimpleRunbook

# Documentation
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

## 2026-01-08t00:41:27.979
- Completed: 2026-01-08t00:41:27.987
- Return Code: 0

### stdout
```
Running SimpleRunbook
Test variable value: FOO
Current directory: /workspace
Listing files:
total 24
drwxr-xr-x 7 root root  224 Jan  8 00:41 .
drwxr-xr-x 1 root root 4096 Jan  8 00:40 ..
-rw-r--r-- 1 root root  122 Jan  7 22:12 CreatePackage.dockerfile
-rw-r--r-- 1 root root  805 Jan  7 22:12 CreatePackage.md
-rw-r--r-- 1 root root  277 Jan  7 22:12 Runbook.md
-rw-r--r-- 1 root root  591 Jan  7 22:12 SimpleRunbook.md
-rwxr-xr-x 1 root root  195 Jan  8 00:41 temp.zsh
SimpleRunbook completed successfully

```

### stderr
```

```

## 2026-01-08t00:43:53.278
- Completed: 2026-01-08t00:43:53.284
- Return Code: 0

### stdout
```
Running SimpleRunbook
Test variable value: test
Current directory: /workspace
Listing files:
total 24
drwxr-xr-x 7 root root  224 Jan  8 00:43 .
drwxr-xr-x 1 root root 4096 Jan  8 00:40 ..
-rw-r--r-- 1 root root  122 Jan  7 22:12 CreatePackage.dockerfile
-rw-r--r-- 1 root root  805 Jan  7 22:12 CreatePackage.md
-rw-r--r-- 1 root root  277 Jan  7 22:12 Runbook.md
-rw-r--r-- 1 root root 1224 Jan  8 00:41 SimpleRunbook.md
-rwxr-xr-x 1 root root  195 Jan  8 00:43 temp.zsh
SimpleRunbook completed successfully

```

### stderr
```

```

## 2026-01-08t00:55:31.203
- Completed: 2026-01-08t00:55:31.209
- Return Code: 0

### stdout
```
Running SimpleRunbook
Test variable value: Test
Current directory: /workspace
Listing files:
total 24
drwxr-xr-x 7 root root  224 Jan  8 00:55 .
drwxr-xr-x 1 root root 4096 Jan  8 00:54 ..
-rw-r--r-- 1 root root  122 Jan  7 22:12 CreatePackage.dockerfile
-rw-r--r-- 1 root root  805 Jan  7 22:12 CreatePackage.md
-rw-r--r-- 1 root root  277 Jan  7 22:12 Runbook.md
-rw-r--r-- 1 root root 1858 Jan  8 00:43 SimpleRunbook.md
-rwxr-xr-x 1 root root  195 Jan  8 00:55 temp.zsh
SimpleRunbook completed successfully

```

### stderr
```

```
