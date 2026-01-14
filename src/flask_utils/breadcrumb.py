from datetime import datetime, timezone
import uuid
import json
import logging
from flask import request
from typing import Optional, List

logger = logging.getLogger(__name__)

def create_flask_breadcrumb(token):
    """
    Create a breadcrumb dictionary from HTTP headers.
    
    Extracts recursion_stack from X-Recursion-Stack header if present.
    If header is missing or invalid, recursion_stack is None (top-level execution).
    
    Args:
        token: Token dictionary with user_id
        
    Returns:
        dict: Breadcrumb with at_time, by_user, from_ip, correlation_id, and recursion_stack
    """
    recursion_stack = None
    
    # Extract recursion_stack from X-Recursion-Stack header
    recursion_stack_header = request.headers.get('X-Recursion-Stack')
    if recursion_stack_header:
        try:
            recursion_stack = json.loads(recursion_stack_header)
            # Validate it's a list
            if not isinstance(recursion_stack, list):
                logger.warning(f"Invalid recursion_stack format (not a list): {recursion_stack_header}")
                recursion_stack = None
            else:
                # Validate all items are strings
                if not all(isinstance(item, str) for item in recursion_stack):
                    logger.warning(f"Invalid recursion_stack format (items must be strings): {recursion_stack_header}")
                    recursion_stack = None
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse X-Recursion-Stack header as JSON: {recursion_stack_header}, error: {e}")
            recursion_stack = None
    
    return {
        "at_time": datetime.now(timezone.utc),
        "by_user": token["user_id"],
        "from_ip": request.remote_addr,  
        "correlation_id": request.headers.get('X-Correlation-Id', str(uuid.uuid4())),
        "recursion_stack": recursion_stack
    }

