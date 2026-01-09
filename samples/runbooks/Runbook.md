# Runbook Template

# Environment Requirements
```yaml
TEST_VAR: A test environment variable for demonstration purposes
```

# File System Requirements
```yaml
Input:
- file spec
Output:
- dir spec
```

# Required Claims
```yaml
roles: developer, admin
```
Optional section. If present, the token must include the specified claims to execute or validate the runbook.
- `roles`: List of roles (comma-separated) that are allowed to execute/validate this runbook
- Other claims can be specified as key-value pairs where the value is a comma-separated list of allowed values

# Script
```sh
#! /bin/zsh
echo "Running"
```

# History
