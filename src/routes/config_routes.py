from flask import Blueprint, jsonify, current_app
from functools import wraps
from ..config.config import Config
from ..flask_utils.token import create_flask_token
from ..flask_utils.breadcrumb import create_flask_breadcrumb
from ..flask_utils.route_wrapper import handle_route_exceptions

import logging
logger = logging.getLogger(__name__)


def _apply_rate_limit(limit_str_getter):
    """Apply rate limiting decorator if rate limiting is enabled."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            config = Config.get_instance()
            if not config.RATE_LIMIT_ENABLED:
                return f(*args, **kwargs)
            try:
                from flask import has_app_context
                if has_app_context() and hasattr(current_app, 'extensions') and 'limiter' in current_app.extensions:
                    limiter = current_app.extensions['limiter']
                    limit_str = limit_str_getter() if callable(limit_str_getter) else limit_str_getter
                    return limiter.limit(limit_str)(f)(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Rate limiting check failed, allowing request: {e}")
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Define the Blueprint for config routes
def create_config_routes():
    config_routes = Blueprint('config_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/config - Return the current configuration as JSON
    @config_routes.route('', methods=['GET'])
    @_apply_rate_limit(lambda: f"{Config.get_instance().RATE_LIMIT_PER_MINUTE} per minute")
    @handle_route_exceptions
    def get_config():
        # Return the JSON representation of the config object
        # Token is automatically validated by create_flask_token()
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        logger.info(f"get_config Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(config.to_dict(token)), 200
        
    logger.info("Config Flask Routes Registered")
    return config_routes

