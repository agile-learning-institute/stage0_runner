# ParentRunbook
This is an example parent runbook that demonstrates calling a sub-runbook (SimpleRunbook.md) via the API. It shows how to use the system-provided environment variables for authentication, correlation tracking, and recursion protection.

# Environment Requirements
```yaml
TEST_VAR: A test environment variable to pass to the child runbook
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

# Script
```sh
#! /bin/zsh
echo "Parent runbook starting"
echo "Correlation ID: $RUNBOOK_CORRELATION_ID"
echo "Recursion stack: $RUNBOOK_RECURSION_STACK"
echo "Runbook URL: $RUNBOOK_URL"

# Call child runbook via API
# The recursion stack already includes this runbook's filename
# Use pre-formatted header variables for easy, correct API calls
echo "Calling SimpleRunbook.md as sub-runbook..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$RUNBOOK_URL/SimpleRunbook.md/execute" \
  -H "$RUNBOOK_H_AUTH" -H "$RUNBOOK_H_CORR" -H "$RUNBOOK_H_RECUR" -H "$RUNBOOK_H_CTYPE" \
  -d "{\"env_vars\":{\"TEST_VAR\":\"${TEST_VAR:-parent_value}\"}}")

# Extract HTTP status code and response body
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "Child runbook executed successfully"
    echo "Response: $BODY"
else
    echo "Child runbook execution failed with HTTP $HTTP_CODE"
    echo "Response: $BODY"
    exit 1
fi

echo "Parent runbook completed successfully"
```

# History
