# CreatePackage
This runbook creates a GitHub Container Registry Package by building a HelloWorld image using [this Dockerfile](./CreatePackage.dockerfile), labeling it to connect to a source code repo, and pushes this new image to ghcr.

# Environment Requirements
```yaml
GITHUB_TOKEN: A github classic token with package:write Privileges
```

# File System Requirements
```yaml
Input:
- ./CreatePackage
- ./CreatePackage.dockerfile
```

# Required Claims
```yaml
roles: sre, api
```
This runbook requires elevated permissions to push to GitHub Container Registry.

# Script
```sh
#! /bin/zsh
# Demo: Display input folder contents
echo "=== Input Folder Contents ==="
cat CreatePackage/input.txt
echo ""
echo "=== Docker Commands (demonstration - not executed) ==="
echo "docker build -f ./CreatePackage.dockerfile"
echo ""
echo "=== Dockerfile Content ==="
cat ./CreatePackage.dockerfile
echo ""
echo "Create Package Completed (demo mode)"
```

# History
