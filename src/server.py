#!/usr/bin/env python3
"""
Flask API server for Stage0 Runbook Runner

Provides REST API endpoints for runbook operations.
Designed to be consumed by a separate SPA frontend.
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from command import RunbookRunner


def create_app(runbooks_dir: str):
    """
    Create and configure Flask application.
    
    Args:
        runbooks_dir: Path to directory containing runbooks
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__, static_folder='../docs', static_url_path='/docs')
    runbooks_path = Path(runbooks_dir).resolve()
    
    def resolve_runbook_path(filename: str) -> Path:
        """Get full path to a runbook file."""
        # Security: prevent directory traversal
        safe_filename = os.path.basename(filename)
        return runbooks_path / safe_filename
    
    def extract_env_vars_from_request():
        """Extract environment variables from query parameters."""
        env_vars = {}
        for key, value in request.args.items():
            if key != 'RUNBOOK':
                env_vars[key] = value
        return env_vars
    
    @app.route('/api/<path:runbook>', methods=['POST'])
    def execute_runbook_path(runbook: str):
        """Execute a runbook (path-based endpoint)."""
        return execute_runbook_impl(runbook)
    
    @app.route('/api/execute', methods=['GET', 'POST'])
    def execute_runbook():
        """Execute a runbook (query parameter-based endpoint)."""
        runbook_filename = request.args.get('RUNBOOK')
        if not runbook_filename:
            return jsonify({
                "success": False,
                "error": "RUNBOOK query parameter is required"
            }), 400
        return execute_runbook_impl(runbook_filename)
    
    def execute_runbook_impl(runbook_filename: str):
        """Execute a runbook implementation."""
        
        runbook_path = resolve_runbook_path(runbook_filename)
        if not runbook_path.exists():
            return jsonify({
                "success": False,
                "error": f"Runbook not found: {runbook_filename}"
            }), 404
        
        # Set environment variables from query params
        env_vars = extract_env_vars_from_request()
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            runner = RunbookRunner(str(runbook_path))
            return_code = runner.execute()
            
            # Reload runbook to get updated content with history
            runner.load_runbook()
            
            # Build viewer link (for SPA integration - adjust URL based on your SPA deployment)
            port = os.environ.get('API_PORT', '5000')
            host = request.host.split(':')[0]  # Get host without port
            # Note: This link should point to your SPA frontend, not a built-in viewer
            viewer_link = f"http://{host}:{port}/runbook/{runbook_filename}"
            
            response = {
                "success": return_code == 0,
                "runbook": runbook_filename,
                "return_code": return_code,
                "viewer_link": viewer_link
            }
            
            # Extract the last execution history from the updated runbook content
            if runner.runbook_content:
                import re
                # Match the last history entry with stdout and stderr in code blocks
                history_pattern = r'## (\d{4}-\d{2}-\d{2}t[\d:\.]+).*?Return Code: (\d+).*?### stdout\s*```\s*\n(.*?)```.*?### stderr\s*```\s*\n(.*?)```'
                matches = list(re.finditer(history_pattern, runner.runbook_content, re.DOTALL))
                if matches:
                    last_match = matches[-1]
                    response["stdout"] = last_match.group(3).strip()
                    response["stderr"] = last_match.group(4).strip()
                else:
                    response["stdout"] = ""
                    response["stderr"] = ""
            else:
                response["stdout"] = ""
                response["stderr"] = ""
            
            response["errors"] = []
            response["warnings"] = []
            
            status_code = 200 if return_code == 0 else 500
            return jsonify(response), status_code
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "runbook": runbook_filename
            }), 500
        finally:
            # Restore original environment variables
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    
    @app.route('/api/<path:runbook>', methods=['PATCH'])
    def validate_runbook_path(runbook: str):
        """Validate a runbook (path-based endpoint)."""
        return validate_runbook_impl(runbook)
    
    @app.route('/api/validate', methods=['GET'])
    def validate_runbook():
        """Validate a runbook (query parameter-based endpoint)."""
        runbook_filename = request.args.get('RUNBOOK')
        if not runbook_filename:
            return jsonify({
                "success": False,
                "error": "RUNBOOK query parameter is required"
            }), 400
        return validate_runbook_impl(runbook_filename)
    
    def validate_runbook_impl(runbook_filename: str):
        """Validate a runbook implementation."""
        
        runbook_path = resolve_runbook_path(runbook_filename)
        if not runbook_path.exists():
            return jsonify({
                "success": False,
                "error": f"Runbook not found: {runbook_filename}"
            }), 404
        
        # Set environment variables from query params
        env_vars = extract_env_vars_from_request()
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            runner = RunbookRunner(str(runbook_path))
            success = runner.validate()
            
            response = {
                "success": success,
                "runbook": runbook_filename,
                "errors": runner.errors,
                "warnings": runner.warnings
            }
            
            status_code = 200 if success else 400
            return jsonify(response), status_code
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "runbook": runbook_filename
            }), 500
        finally:
            # Restore original environment variables
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    
    @app.route('/api/runbooks', methods=['GET'])
    def list_runbooks():
        """List all available runbooks."""
        if not runbooks_path.exists():
            return jsonify({
                "success": False,
                "error": f"Runbooks directory not found: {runbooks_path}"
            }), 404
        
        runbooks = []
        for file_path in runbooks_path.glob('*.md'):
            try:
                runner = RunbookRunner(str(file_path))
                if runner.load_runbook():
                    runbooks.append({
                        "filename": file_path.name,
                        "name": runner.runbook_name,
                        "path": str(file_path.relative_to(runbooks_path))
                    })
            except Exception:
                # Skip files that can't be loaded as runbooks
                continue
        
        return jsonify({
            "success": True,
            "runbooks": sorted(runbooks, key=lambda x: x['filename'])
        })
    
    @app.route('/api/<path:runbook>', methods=['GET'])
    def get_runbook_by_path(runbook: str):
        """Get runbook content (path-based endpoint)."""
        return get_runbook_impl(runbook)
    
    @app.route('/api/runbooks/<filename>', methods=['GET'])
    def get_runbook(filename: str):
        """Get runbook content (legacy endpoint)."""
        return get_runbook_impl(filename)
    
    def get_runbook_impl(filename: str):
        """Get runbook content implementation."""
        runbook_path = resolve_runbook_path(filename)
        if not runbook_path.exists():
            return jsonify({
                "success": False,
                "error": f"Runbook not found: {filename}"
            }), 404
        
        try:
            with open(runbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            runner = RunbookRunner(str(runbook_path))
            runner.load_runbook()
            
            return jsonify({
                "success": True,
                "filename": filename,
                "name": runner.runbook_name,
                "content": content
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "filename": filename
            }), 500
    
    return app

