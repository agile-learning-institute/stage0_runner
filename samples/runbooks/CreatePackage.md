# CreatePackage
This runbook creates a GitHub Container Registry Package by building a HelloWorld image using [this Dockerfile](./CreatePackage.dockerfile), labeling it to connect to a source code repo, and pushes this new image to ghcr.

# Environment Requirements
```yaml
GITHUB_TOKEN: A github classic token with package:write Privileges
```

# File System Requirements
```yaml
Input:
- ./CreatePackage.dockerfile
Output:
```

# Required Claims
```yaml
roles: developer, admin, devops
```
This runbook requires elevated permissions to push to GitHub Container Registry.

# Script
```sh
#! /bin/zsh
echo $GITHUB_TOKEN | docker login ghcr.io -u agile-crafts-people --password-stdin && \
docker build -f DeveloperEdition/sre_resources/Dockerfile.ghcr-package --build-arg REPO=$(REPO) -t ghcr.io/agile-crafts-people/$(REPO):latest .
docker push ghcr.io/agile-crafts-people/$(REPO):latest
echo Create Package Completed
```

# History
