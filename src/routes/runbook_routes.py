"""
Runbook routes for Flask API.

Provides endpoints for Runbook domain:
- GET /api/runbooks - List all runbooks
- GET /api/runbooks/<filename> - Get a specific runbook
- GET /api/runbooks/<filename>/required-env - Get required environment variables
- POST /api/runbooks/<filename>/execute - Execute a runbook
- PATCH /api/runbooks/<filename>/validate - Validate a runbook
"""
from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from ..flask_utils.token import create_flask_token
from ..flask_utils.breadcrumb import create_flask_breadcrumb
from ..flask_utils.route_wrapper import handle_route_exceptions
from ..services.runbook_service import RunbookService
from ..config.config import Config

import logging
logger = logging.getLogger(__name__)


def _apply_rate_limit(limit_str_getter):
    """
    Apply rate limiting decorator if rate limiting is enabled.
    
    Args:
        limit_str_getter: Callable that returns the rate limit string (e.g., "10 per minute")
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            config = Config.get_instance()
            if not config.RATE_LIMIT_ENABLED:
                # Rate limiting disabled, call function normally
                return f(*args, **kwargs)
            
            try:
                # Get limiter from current app context
                from flask import has_app_context
                if has_app_context() and hasattr(current_app, 'extensions') and 'limiter' in current_app.extensions:
                    limiter = current_app.extensions['limiter']
                    # Get limit string
                    limit_str = limit_str_getter() if callable(limit_str_getter) else limit_str_getter
                    # Apply rate limit decorator at runtime
                    # Flask-Limiter will raise RateLimitExceeded (429) if limit exceeded
                    return limiter.limit(limit_str)(f)(*args, **kwargs)
            except Exception as e:
                # If rate limiting fails, log and continue (fail open)
                logger.warning(f"Rate limiting check failed, allowing request: {e}")
            
            # Fallback: call function normally if rate limiting unavailable
            return f(*args, **kwargs)
        
        return wrapper
    return decorator


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
    @_apply_rate_limit(lambda: f"{Config.get_instance().RATE_LIMIT_PER_MINUTE} per minute")
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
    @_apply_rate_limit(lambda: f"{Config.get_instance().RATE_LIMIT_PER_MINUTE} per minute")
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
    @_apply_rate_limit(lambda: f"{Config.get_instance().RATE_LIMIT_PER_MINUTE} per minute")
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
    @_apply_rate_limit(lambda: f"{Config.get_instance().RATE_LIMIT_PER_MINUTE} per minute")
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
    @_apply_rate_limit(lambda: f"{Config.get_instance().RATE_LIMIT_EXECUTE_PER_MINUTE} per minute")
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
            
        Returns:
            JSON response with execution result
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Extract environment variables from request body
        env_vars = {}
        if request.is_json and request.json:
            env_vars.update(request.json.get('env_vars', {}))
        
        result = runbook_service.execute_runbook(filename, token, breadcrumb, env_vars)
        logger.info(f"execute_runbook Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    
    logger.info("Runbook Flask Routes Registered")
    return runbook_routes

