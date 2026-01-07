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


## 2026-01-07t16:35:05.781
Completed: 2026-01-07t16:35:05.788
Return Code: 0

### stdout
```
Running SimpleRunbook
Test variable value: test_execution_value
Current directory: /Users/mikestorey/source/agile-learning-institute/stageZero/stage0_runner/samples/runbooks
Listing files:
total 40
drwxr-xr-x@ 7 mikestorey  staff  224 Jan  7 16:35 .
drwxr-xr-x@ 6 mikestorey  staff  192 Jan  7 16:34 ..
-rw-r--r--@ 1 mikestorey  staff  122 Jan  7 14:07 CreatePackage.dockerfile
-rw-r--r--@ 1 mikestorey  staff  805 Jan  7 14:13 CreatePackage.md
-rw-r--r--@ 1 mikestorey  staff  277 Jan  7 15:18 Runbook.md
-rw-r--r--@ 1 mikestorey  staff  592 Jan  7 16:15 SimpleRunbook.md
-rwxr-xr-x@ 1 mikestorey  staff  195 Jan  7 16:35 temp.zsh
SimpleRunbook completed successfully

```

### stderr
```

```
