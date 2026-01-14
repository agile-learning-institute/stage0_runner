#!/usr/bin/env python3
"""
Test utilities for runbook test cleanup and restoration.

Provides utilities to save and restore runbook files that are modified during tests.
"""
import subprocess
from pathlib import Path
from typing import Optional, Dict

# Track original content of runbooks
_ORIGINAL_RUNBOOK_CONTENT: Dict[str, str] = {}


def save_runbook(runbook_path: Path) -> None:
    """Save the original content of a runbook file."""
    if runbook_path.exists():
        with open(runbook_path, 'r', encoding='utf-8') as f:
            _ORIGINAL_RUNBOOK_CONTENT[str(runbook_path)] = f.read()


def restore_runbook(runbook_path: Path) -> None:
    """Restore a runbook file to its original state using git, with fallback to saved content."""
    # Use git to discard any changes (this is the primary method)
    try:
        repo_root = Path(__file__).parent.parent
        subprocess.run(
            ['git', 'checkout', '--', str(runbook_path)],
            cwd=repo_root,
            capture_output=True,
            check=False
        )
    except Exception:
        pass  # Git restore is best-effort
    
    # Fallback: restore from saved content if git didn't work
    runbook_key = str(runbook_path)
    if runbook_key in _ORIGINAL_RUNBOOK_CONTENT and runbook_path.exists():
        try:
            with open(runbook_path, 'w', encoding='utf-8') as f:
                f.write(_ORIGINAL_RUNBOOK_CONTENT[runbook_key])
        except Exception:
            pass  # Best-effort restoration


def save_all_test_runbooks() -> None:
    """Save original content of all runbooks used in tests."""
    repo_root = Path(__file__).parent.parent
    runbooks_dir = repo_root / 'samples' / 'runbooks'
    
    # Save SimpleRunbook.md, ParentRunbook.md, and CreatePackage.md (the ones used in tests)
    for runbook_name in ['SimpleRunbook.md', 'ParentRunbook.md', 'CreatePackage.md']:
        runbook_path = runbooks_dir / runbook_name
        if runbook_path.exists():
            save_runbook(runbook_path)


def restore_all_test_runbooks() -> None:
    """Restore all test runbooks to their original state."""
    repo_root = Path(__file__).parent.parent
    runbooks_dir = repo_root / 'samples' / 'runbooks'
    
    # Restore SimpleRunbook.md, ParentRunbook.md, and CreatePackage.md
    for runbook_name in ['SimpleRunbook.md', 'ParentRunbook.md', 'CreatePackage.md']:
        runbook_path = runbooks_dir / runbook_name
        if runbook_path.exists():
            restore_runbook(runbook_path)
