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


## 2026-01-07t14:35:52.648
Completed: 2026-01-07t14:35:52.656
Return Code: 0

### stdout
Running SimpleRunbook
Test variable value: test_execution_value
Current directory: /Users/mikestorey/source/agile-learning-institute/stageZero/stage0_runner/test/runbooks
Listing files:
total 32
drwxr-xr-x@ 6 mikestorey  staff  192 Jan  7 14:35 .
drwxr-xr-x@ 4 mikestorey  staff  128 Jan  7 13:50 ..
-rw-r--r--@ 1 mikestorey  staff  122 Jan  7 14:07 CreatePackage.dockerfile
-rw-r--r--@ 1 mikestorey  staff  805 Jan  7 14:13 CreatePackage.md
-rw-r--r--@ 1 mikestorey  staff  592 Jan  7 14:34 SimpleRunbook.md
-rwxr-xr-x@ 1 mikestorey  staff  195 Jan  7 14:35 temp.zsh
SimpleRunbook completed successfully


### stderr


## 2026-01-07t14:36:13.628
Completed: 2026-01-07t14:36:13.635
Return Code: 0

### stdout
Running SimpleRunbook
Test variable value: test_execution_value
Current directory: /Users/mikestorey/source/agile-learning-institute/stageZero/stage0_runner/test/runbooks
Listing files:
total 32
drwxr-xr-x@ 6 mikestorey  staff   192 Jan  7 14:36 .
drwxr-xr-x@ 4 mikestorey  staff   128 Jan  7 13:50 ..
-rw-r--r--@ 1 mikestorey  staff   122 Jan  7 14:07 CreatePackage.dockerfile
-rw-r--r--@ 1 mikestorey  staff   805 Jan  7 14:13 CreatePackage.md
-rw-r--r--@ 1 mikestorey  staff  1301 Jan  7 14:35 SimpleRunbook.md
-rwxr-xr-x@ 1 mikestorey  staff   195 Jan  7 14:36 temp.zsh
SimpleRunbook completed successfully


### stderr

