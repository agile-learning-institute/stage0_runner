# Runbooks

A runbook is a markdown file, with some specific layout requirements. The document will have six H1 headers, with the following content:

# RunbookName
The first H1 should be the runbook name. This should match the file name, without the .md extension. Runbook file names should not contain spaces. By convention, runbooks use Pascal case names. 

# Documentation
This is where you will find a description of what the runbook does, when to use it, and how to use it.

# Environment Requirements
This section must contain a yaml code block that defines the environment variables that the script expects to find, with a description of what that variable should contain. 
```yaml
REPO: The name of the repo in the form org/repo
GITHUB_TOKEN: A github classic token with xyz permissions
```

# File System Requirements
This section must contain information about what files and folders should be in place for the script to run. The file naming convention RunbookName.someType if there is only one or two files. If there are many files, you can create a folder with the RunbookName and store the files there. If the script creates output files, you can specify output folders that should available.
```yaml
Input:
- ./Runbook.dockerfile
- ./Runbook/one_of_many_files.csv
Output:
- /some/output/folder
```

# Required Claims
This section is optional. If present, it specifies the JWT claims required to execute or validate the runbook. This enables Role-Based Access Control (RBAC).

```yaml
# Required Claims
roles: developer, admin, devops
```

When executing or validating a runbook:
1. The API extracts required claims from the runbook
2. Validates that the user's token contains the required claims
3. If validation fails, returns 403 Forbidden and logs the attempt to runbook history
4. If validation succeeds, proceeds with operation

You can specify multiple claim types:
```yaml
# Required Claims
roles: developer, admin
environment: production
team: platform-engineering
```

The token must have at least one matching value for each required claim.

# Script
This section must contain a sh code block with the runbook script
```sh
#! /bin/zsh
some zsh script code
```

# History
At the bottom of the document will be a history section where executions are recorded. This has to be at the bottom of the document, as executions will append their run data to the file.

## History Format

Execution history is stored as minified JSON (single line, no whitespace) in the runbook's History section. Each execution or validation operation appends a history entry to the runbook file and logs the same value. The history document schema is described [here](./docs/history-schema.json).

Each history entry contains:
- `start_timestamp` - ISO 8601 timestamp when execution started
- `finish_timestamp` - ISO 8601 timestamp when execution finished
- `return_code` - Exit code from script execution (0 = success, non-zero = failure)
- `operation` - Operation type (`execute` or `validate`)
- `breadcrumb` - Request metadata including user ID, roles, correlation ID, timestamp
- `config_items` - Configuration values active during execution (secrets masked)
- `stdout` - Standard output from script execution
- `stderr` - Standard error from script execution
- `errors` - List of validation or execution errors
- `warnings` - List of warnings

Example history entry (minified JSON):
```json
{"start_timestamp":"2026-01-23T14:32:15.314Z","finish_timestamp":"2026-01-23T14:33:02.123Z","return_code":0,"operation":"execute","breadcrumb":{"user_id":"user123","roles":["developer"],"correlation_id":"abc-123","at_time":"2026-01-23T14:32:15.314Z"},"config_items":[...],"stdout":"Script output here","stderr":"","errors":[],"warnings":[]}
```

## Execution Processing

When a runbook is executed, the API follows this process:

1. **Validate runbook structure and requirements** (fail-fast)
   - Check all required sections are present
   - Verify required environment variables are set
   - Verify required input files exist
   - Validate script section contains executable code

2. **Check RBAC permissions** based on required claims
   - Extract required claims from runbook (if present)
   - Validate user's token contains required claims
   - Log RBAC failures to runbook history

3. **Create isolated temporary directory** for script execution
   - Creates unique temp directory per execution
   - Prevents path traversal attacks

4. **Create temp.zsh** with the contents of the script
   - Sets executable permissions (0o700 - owner-only)

5. **Invoke temp.zsh** and capture stdout and stderr
   - Executes with configurable timeout
   - Applies output size limits
   - Captures return code

6. **Append execution history** as minified JSON to runbook
   - Appends to History section
   - Includes all execution metadata

7. **Log execution history** to application logs
   - Same JSON format as file history

8. **Remove temp.zsh** and cleanup temporary directory
   - Automatic cleanup even on errors
