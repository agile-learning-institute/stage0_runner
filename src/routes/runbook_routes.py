"""
Runbook routes for Flask API.

Provides endpoints for Runbook domain:
- GET /api/runbooks - List all runbooks
- GET /api/runbooks/<filename> - Get a specific runbook
- GET /api/runbooks/<filename>/required-env - Get required environment variables
- POST /api/runbooks/<filename>/execute - Execute a runbook
- PATCH /api/runbooks/<filename>/validate - Validate a runbook
"""
from flask import Blueprint, jsonify, request
from ..flask_utils.token import create_flask_token
from ..flask_utils.breadcrumb import create_flask_breadcrumb
from ..flask_utils.route_wrapper import handle_route_exceptions
from ..services.runbook_service import RunbookService
from ..config.config import Config

import logging
logger = logging.getLogger(__name__)


def create_runbook_routes(runbooks_dir: str):
    """
    Create a Flask Blueprint exposing runbook endpoints.
    
    Args:
        runbooks_dir: Path to directory containing runbooks
    
    Returns:
        Blueprint: Flask Blueprint with runbook routes
    """
    runbook_routes = Blueprint('runbook_routes', __name__)
    runbook_service = RunbookService(runbooks_dir)
    
    @runbook_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def list_runbooks():
        """
        GET /api/runbooks - List all available runbooks.
        
        Returns:
            JSON response with list of runbooks
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        result = runbook_service.list_runbooks(token, breadcrumb)
        logger.info(f"list_runbooks Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @runbook_routes.route('/<filename>', methods=['GET'])
    @handle_route_exceptions
    def get_runbook(filename: str):
        """
        GET /api/runbooks/<filename> - Get runbook content.
        
        Args:
            filename: The runbook filename
            
        Returns:
            JSON response with runbook content and metadata
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        result = runbook_service.get_runbook(filename, token, breadcrumb)
        logger.info(f"get_runbook Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @runbook_routes.route('/<filename>/required-env', methods=['GET'])
    @handle_route_exceptions
    def get_required_env(filename: str):
        """
        GET /api/runbooks/<filename>/required-env - Get required environment variables.
        
        Args:
            filename: The runbook filename
            
        Returns:
            JSON response with required, available, and missing environment variables
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        result = runbook_service.get_required_env(filename, token, breadcrumb)
        logger.info(f"get_required_env Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @runbook_routes.route('/<filename>/validate', methods=['PATCH'])
    @handle_route_exceptions
    def validate_runbook(filename: str):
        """
        PATCH /api/runbooks/<filename>/validate - Validate a runbook.
        
        Args:
            filename: The runbook filename
            
        Returns:
            JSON response with validation result
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        result = runbook_service.validate_runbook(filename, token, breadcrumb)
        logger.info(f"validate_runbook Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    
    @runbook_routes.route('/<filename>/execute', methods=['POST'])
    @handle_route_exceptions
    def execute_runbook(filename: str):
        """
        POST /api/runbooks/<filename>/execute - Execute a runbook.
        
        Args:
            filename: The runbook filename
            
        Request body (optional):
            {
                "env_vars": {
                    "VAR_NAME": "value"
                }
            }
            
        Query parameters (optional):
            - Any query parameters will be treated as environment variables
            
        Returns:
            JSON response with execution result
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Extract environment variables from request body or query parameters
        env_vars = {}
        if request.is_json and request.json:
            env_vars.update(request.json.get('env_vars', {}))
        
        # Also allow env vars from query parameters (for backward compatibility)
        for key, value in request.args.items():
            if key not in ['RUNBOOK']:  # Skip special parameters
                env_vars[key] = value
        
        result = runbook_service.execute_runbook(filename, token, breadcrumb, env_vars)
        logger.info(f"execute_runbook Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    
    logger.info("Runbook Flask Routes Registered")
    return runbook_routes

