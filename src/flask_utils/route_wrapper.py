"""
Flask route wrapper utility for exception handling.
"""
from functools import wraps
from flask import jsonify
from .exceptions import HTTPUnauthorized, HTTPForbidden, HTTPNotFound, HTTPInternalServerError
import logging

logger = logging.getLogger(__name__)


def handle_route_exceptions(f):
    """
    Decorator to handle custom HTTP exceptions in Flask routes.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPUnauthorized as e:
            logger.warning(f"HTTPUnauthorized: {e.message}")
            return jsonify({"error": e.message}), e.status_code
        except HTTPForbidden as e:
            logger.warning(f"HTTPForbidden: {e.message}")
            return jsonify({"error": e.message}), e.status_code
        except HTTPNotFound as e:
            logger.info(f"HTTPNotFound: {e.message}")
            return jsonify({"error": e.message}), e.status_code
        except HTTPInternalServerError as e:
            logger.error(f"HTTPInternalServerError: {e.message}")
            return jsonify({"error": e.message}), e.status_code
        except Exception as e:
            # Handle Flask-Limiter RateLimitExceeded exception
            if hasattr(e, 'status_code') and e.status_code == 429:
                logger.warning(f"Rate limit exceeded: {str(e)}")
                return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
            logger.error(f"Unexpected error in route {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({"error": "A processing error occurred"}), 500
    return decorated_function

