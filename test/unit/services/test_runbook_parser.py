#!/usr/bin/env python3
"""
Unit tests for RunbookParser (focusing on parse_last_history_entry).
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.services.runbook_parser import RunbookParser


class TestRunbookParserHistoryParsing:
    """Test parse_last_history_entry method."""
    
    def test_parse_last_history_entry_with_valid_markdown(self):
        """Test parsing last history entry with valid markdown format."""
        content = """# Test Runbook

# History

### 2024-01-01T00:00:00.000Z | Exit Code: 0

**Stdout:**
```
output1
```

**Stderr:**
```
error1
```

### 2024-01-01T00:01:00.000Z | Exit Code: 1

**Stdout:**
```
output2
```

**Stderr:**
```
error2
```
"""
        stdout, stderr = RunbookParser.parse_last_history_entry(content)
        assert stdout == "output2"
        assert stderr == "error2"
    
    def test_parse_last_history_entry_no_history_section(self):
        """Test parsing when History section doesn't exist."""
        content = "# Test Runbook\n\n# Environment Requirements\n```yaml\n```\n# Script\n```sh\necho test\n```"
        stdout, stderr = RunbookParser.parse_last_history_entry(content)
        assert stdout == ""
        assert stderr == ""
    
    def test_parse_last_history_entry_empty_content(self):
        """Test parsing with empty content."""
        stdout, stderr = RunbookParser.parse_last_history_entry("")
        assert stdout == ""
        assert stderr == ""
    
    def test_parse_last_history_entry_no_history_entries(self):
        """Test parsing when History section exists but has no entries."""
        content = "# Test Runbook\n\n# History\n\nSome text"
        stdout, stderr = RunbookParser.parse_last_history_entry(content)
        assert stdout == ""
        assert stderr == ""
    
    def test_parse_last_history_entry_stdout_only(self):
        """Test parsing when only stdout is present."""
        content = """# Test Runbook

# History

### 2024-01-01T00:00:00.000Z | Exit Code: 0

**Stdout:**
```
some output
```
"""
        stdout, stderr = RunbookParser.parse_last_history_entry(content)
        assert stdout == "some output"
        assert stderr == ""
    
    def test_parse_last_history_entry_stderr_only(self):
        """Test parsing when only stderr is present."""
        content = """# Test Runbook

# History

### 2024-01-01T00:00:00.000Z | Exit Code: 1

**Stderr:**
```
some error
```
"""
        stdout, stderr = RunbookParser.parse_last_history_entry(content)
        assert stdout == ""
        assert stderr == "some error"
    
    def test_parse_last_history_entry_with_escaped_code_fences(self):
        """Test parsing when stdout/stderr contain code fence delimiters."""
        content = """# Test Runbook

# History

### 2024-01-01T00:00:00.000Z | Exit Code: 0

**Stdout:**
```
Some output with \\`\\`\\` code
```
"""
        stdout, stderr = RunbookParser.parse_last_history_entry(content)
        assert "```" in stdout

