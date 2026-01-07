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
