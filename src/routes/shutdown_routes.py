"""
Shutdown routes for Flask API.

Provides endpoint for graceful server shutdown.
"""
from flask import Blueprint, jsonify, request
from ..flask_utils.token import create_flask_token
from ..flask_utils.route_wrapper import handle_route_exceptions
from ..flask_utils.exceptions import HTTPInternalServerError
import os
import signal
import threading
import logging

logger = logging.getLogger(__name__)

# Global shutdown flag for Gunicorn
shutdown_flag = threading.Event()


def create_shutdown_routes():
    """
    Create a Flask Blueprint for shutdown endpoint.
    
    Returns:
        Blueprint: Flask Blueprint with shutdown route
    """
    shutdown_routes = Blueprint('shutdown_routes', __name__)
    
    @shutdown_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def shutdown():
        """
        POST /api/shutdown - Gracefully shutdown the server.
        
        Requires any valid JWT token (no specific claims needed).
        
        Returns:
            JSON response with shutdown message
        """
        # Require valid JWT token (any token, no claims check)
        token = create_flask_token()
        logger.info(f"Shutdown requested by user {token.get('user_id')}")
        
        # Try Flask dev server shutdown first
        shutdown_func = request.environ.get('werkzeug.server.shutdown')
        if shutdown_func:
            shutdown_func()
            return jsonify({"message": "Server shutting down"}), 200
        
        # For Gunicorn, set shutdown flag and send SIGTERM to master process
        shutdown_flag.set()
        
        # Send SIGTERM to current process (Gunicorn master will handle gracefully)
        # Get the parent process ID (Gunicorn master)
        try:
            # In Gunicorn, the worker process can trigger shutdown via the master
            # We send SIGTERM to the current process group
            os.kill(os.getpid(), signal.SIGTERM)
        except Exception as e:
            logger.error(f"Error sending shutdown signal: {e}")
            raise HTTPInternalServerError("Shutdown not available in this environment")
        
        return jsonify({"message": "Shutdown initiated"}), 200
    
    logger.info("Shutdown Flask Routes Registered")
    return shutdown_routes

