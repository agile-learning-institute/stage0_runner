#!/usr/bin/env python3
"""
Update the coverage report markdown file.
"""
import json
from pathlib import Path

# Read coverage data
with open('coverage.json', 'r') as f:
    coverage_data = json.load(f)

# Get line counts for each file
files_data = []
for filepath, data in coverage_data['files'].items():
    total_lines = data['summary']['num_statements']
    covered_lines = data['summary']['covered_lines']
    missing_lines = data['summary']['missing_lines']
    coverage_pct = data['summary']['percent_covered']
    
    try:
        with open(filepath, 'r') as f:
            file_lines = len(f.readlines())
    except:
        file_lines = total_lines
    
    rel_path = filepath.replace(str(Path.cwd()) + '/', '')
    
    files_data.append({
        'file': rel_path,
        'total_lines': file_lines,
        'statements': total_lines,
        'covered': covered_lines,
        'missing': missing_lines,
        'coverage': coverage_pct
    })

files_data.sort(key=lambda x: x['file'])

# Generate markdown report
report = []
report.append("# Test Coverage Report")
report.append("")
report.append(f"**Overall Coverage: {coverage_data['totals']['percent_covered']:.1f}%**")
report.append(f"- Total Statements: {coverage_data['totals']['num_statements']}")
report.append(f"- Covered: {coverage_data['totals']['covered_lines']}")
report.append(f"- Missing: {coverage_data['totals']['missing_lines']}")
report.append("")
report.append("## Coverage by File")
report.append("")
report.append("| File | Total Lines | Statements | Covered | Missing | Coverage % | Status |")
report.append("|------|-------------|------------|---------|---------|------------|--------|")

for file_data in files_data:
    status = "✓ Good" if file_data['coverage'] >= 80 else "⚠ Low" if file_data['coverage'] >= 60 else "✗ Poor"
    report.append(f"| {file_data['file']} | {file_data['total_lines']} | {file_data['statements']} | {file_data['covered']} | {file_data['missing']} | {file_data['coverage']:.1f}% | {status} |")

report.append("")
report.append("## Summary")
report.append("")
good = sum(1 for f in files_data if f['coverage'] >= 80)
low = sum(1 for f in files_data if 60 <= f['coverage'] < 80)
poor = sum(1 for f in files_data if f['coverage'] < 60)
report.append(f"- **Good (≥80%):** {good} files")
report.append(f"- **Low (60-79%):** {low} files")
report.append(f"- **Poor (<60%):** {poor} files")

with open('COVERAGE_REPORT.md', 'w') as f:
    f.write('\n'.join(report))

print('Coverage report updated: COVERAGE_REPORT.md')
