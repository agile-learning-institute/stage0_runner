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
    
    def test_parse_last_history_entry_with_valid_json(self):
        """Test parsing last history entry with valid JSON."""
        content = """# Test Runbook

# History
{"start_timestamp":"2024-01-01T00:00:00.000Z","stdout":"output1","stderr":"error1"}
{"start_timestamp":"2024-01-01T00:01:00.000Z","stdout":"output2","stderr":"error2"}
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
    
    def test_parse_last_history_entry_no_json_lines(self):
        """Test parsing when no JSON lines exist."""
        content = "# Test Runbook\n\n# History\n\nSome text"
        stdout, stderr = RunbookParser.parse_last_history_entry(content)
        assert stdout == ""
        assert stderr == ""

