"""
Dev Login routes for Flask services.

Provides a /dev-login endpoint that issues signed JWTs for local / dev environments.
This endpoint is only enabled when Config.ENABLE_LOGIN is True.
"""
from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from ..config.config import Config
from ..flask_utils.route_wrapper import handle_route_exceptions
from ..flask_utils.exceptions import HTTPNotFound, HTTPForbidden
from datetime import datetime, timedelta, timezone
import jwt

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
            
            # Get limit string - if None, skip rate limiting (e.g., for OPTIONS)
            limit_str = limit_str_getter() if callable(limit_str_getter) else limit_str_getter
            if limit_str is None:
                return f(*args, **kwargs)
            
            try:
                from flask import has_app_context
                if has_app_context() and hasattr(current_app, 'extensions') and 'limiter' in current_app.extensions:
                    limiter = current_app.extensions['limiter']
                    return limiter.limit(limit_str)(f)(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Rate limiting check failed, allowing request: {e}")
            return f(*args, **kwargs)
        return wrapper
    return decorator


def create_dev_login_routes():
    """
    Create a Flask Blueprint for dev-login endpoint.
    
    Returns:
        Blueprint: Flask Blueprint with dev-login route (always returned)
    """
    dev_login_routes = Blueprint('dev_login_routes', __name__)
    config = Config.get_instance()
    
    @dev_login_routes.route('', methods=['POST', 'OPTIONS'])
    @_apply_rate_limit(lambda: f"{Config.get_instance().RATE_LIMIT_EXECUTE_PER_MINUTE} per minute" if request.method == 'POST' else None)
    @handle_route_exceptions
    def dev_login():
        """
        POST /dev-login - Issue a signed JWT for development.
        
        Request body (JSON, all fields optional):
        {
            "subject": "dev-user-1",
            "roles": ["developer", "admin"]
        }
        """
        # Handle CORS preflight requests (OPTIONS bypasses rate limiting via decorator)
        if request.method == 'OPTIONS':
            response = jsonify({})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            return response, 200
        
        # Check if dev login is enabled
        config = Config.get_instance()
        if not config.ENABLE_LOGIN:
            raise HTTPNotFound("Not found")
        
        # Get request data
        data = request.get_json() or {}
        subject = data.get('subject', 'dev-user-1')
        roles = data.get('roles', ['developer'])
        
        # Build JWT claims
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=config.JWT_TTL_MINUTES)
        
        claims = {
            "iss": config.JWT_ISSUER,
            "aud": config.JWT_AUDIENCE,
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "roles": roles
        }
        
        # Generate JWT
        try:
            token = jwt.encode(
                claims,
                config.JWT_SECRET,
                algorithm=config.JWT_ALGORITHM
            )
        except Exception as e:
            logger.error(f"Error encoding JWT: {str(e)}")
            raise HTTPForbidden(f"Error generating token: {str(e)}")
        
        # Return response with CORS headers
        response = {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": exp.isoformat(),
            "subject": subject,
            "roles": roles
        }
        
        logger.info(f"Dev login successful for subject: {subject}")
        response_obj = jsonify(response)
        response_obj.headers.add('Access-Control-Allow-Origin', '*')
        response_obj.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response_obj.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response_obj, 200
    
    logger.info("Dev Login Flask Routes Registered")
    return dev_login_routes

