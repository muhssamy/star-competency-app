# star_competency_app/utils/security_logging.py
import json
import logging
import os
import time

from flask import g, has_request_context, request, session
from flask_login import current_user

logger = logging.getLogger("security")


class SecurityLogFilter(logging.Filter):
    """Filter for enhancing security logs with additional info."""

    def filter(self, record):
        # Set default values for all fields to ensure they always exist
        record.request_id = "no-request-id"
        record.user_id = "anonymous"
        record.ip_address = "no-request-context"
        record.timestamp = time.time()

        # Only try to get context-specific values if in a request context
        if has_request_context():
            # Add request ID if available
            if hasattr(g, "request_id"):
                record.request_id = g.request_id

            # Add user ID if available
            try:
                if (
                    hasattr(current_user, "is_authenticated")
                    and current_user.is_authenticated
                    and hasattr(current_user, "id")
                ):
                    record.user_id = current_user.id
                elif "user" in session and "id" in session["user"]:
                    record.user_id = session["user"]["id"]
            except Exception:
                # Just use the default anonymous value if anything fails
                pass

            # Add IP address
            try:
                # Try to get real IP if behind proxy
                if request.headers.get("X-Forwarded-For"):
                    record.ip_address = (
                        request.headers.get("X-Forwarded-For").split(",")[0].strip()
                    )
                # Fall back to remote_addr
                elif request.remote_addr:
                    record.ip_address = request.remote_addr
            except Exception:
                # Keep the default no-request-context if anything fails
                pass

        return True


def setup_security_logging(app):
    """Setup security logging for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(app.root_path, "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Create handler
    handler = logging.FileHandler(os.path.join(logs_dir, "security.log"))

    # Use a formatter that doesn't fail if fields are missing
    formatter = logging.Formatter(
        "%(asctime)s [%(request_id)s] [User:%(user_id)s] [IP:%(ip_address)s] "
        "%(levelname)s: %(message)s"
    )
    handler.setFormatter(formatter)

    # Configure logger
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.INFO)

    # Add filter that ensures all required fields exist
    security_logger.addFilter(SecurityLogFilter())

    # Remove existing handlers to avoid duplicates if setup is called multiple times
    for hdlr in security_logger.handlers[:]:
        security_logger.removeHandler(hdlr)

    security_logger.addHandler(handler)

    # Prevent propagation to the root logger to avoid duplicate log entries
    security_logger.propagate = False

    return security_logger


def log_security_event(event_type, details, level=logging.INFO):
    """Log a security event."""
    security_logger = logging.getLogger("security")

    # Convert details to string if it's a dict
    if isinstance(details, dict):
        details_str = json.dumps(details)
    else:
        details_str = str(details)

    message = f"{event_type}: {details_str}"
    security_logger.log(level, message)


def log_login(user_id, success, ip_address=None, username=None):
    """Log a login attempt."""
    details = {"user_id": user_id, "success": success}

    if ip_address:
        details["ip_address"] = ip_address

    if username:
        details["username"] = username

    log_level = logging.INFO if success else logging.WARNING
    log_security_event("LOGIN_ATTEMPT", details, log_level)


def log_access(user_id, resource, action, success):
    """Log an access control event."""
    details = {
        "user_id": user_id,
        "resource": resource,
        "action": action,
        "success": success,
    }

    log_level = logging.INFO if success else logging.WARNING
    log_security_event("ACCESS_CONTROL", details, log_level)


def log_data_access(user_id, data_type, record_id, action):
    """Log data access event."""
    details = {
        "user_id": user_id,
        "data_type": data_type,
        "record_id": record_id,
        "action": action,
    }

    log_security_event("DATA_ACCESS", details, logging.INFO)


def log_api_call(user_id, endpoint, method, status_code):
    """Log API call."""
    details = {
        "user_id": user_id,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
    }

    log_level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
    log_security_event("API_CALL", details, log_level)
