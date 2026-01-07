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

# Script
This section must contain a sh code block with the runbook script
```sh
#! /bin/zsh
some zsh script code
```

# History
At the bottom of the document will be a history section where executions are recorded. This has to be at the bottom of the document, as executions will append their run data to the file.

## 2026-01-23t14:32:15.314
Completed: 2026-01-23t14:33:02.123
Return Code: 0

### stdout
This is std out from the execution

### stderr
This is std err from the execution
