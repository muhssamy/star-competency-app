# star_competency_app/utils/security_middleware.py
import time
import uuid
from functools import wraps

from flask import abort, current_app, g, request, session


def security_headers(response):
    """Add security headers to all responses."""
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:;"
    )

    # Prevent browsers from MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # XSS Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    # HTTP Strict Transport Security
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


def security_before_request():
    """Security checks before processing a request."""
    # Add request ID for tracing
    g.request_id = str(uuid.uuid4())

    # Define public routes that don't require authentication
    public_endpoints = [
        "auth.login",  # Login page
        "auth.callback",  # Azure SSO callback
        "static",  # Static assets
        "auth.logout",  # Logout should be accessible if session expires
        "index",  # Root route (/)
    ]

    # Check if current route is a public endpoint
    if request.endpoint in public_endpoints:
        return  # Allow access to public routes without session checks

    # Check if user is authenticated
    if "user" not in session:
        return abort(401)  # Unauthorized - not logged in

    # Check session expiry
    if "last_activity" in session:
        # Session timeout after 30 minutes of inactivity
        if time.time() - session["last_activity"] > 1800:  # 30 minutes
            session.clear()
            return abort(401)  # Unauthorized - session expired

    # Update last activity
    session["last_activity"] = time.time()


def init_security(app):
    """Initialize security features for the Flask app."""
    # Register middleware
    app.after_request(security_headers)
    app.before_request(security_before_request)

    # Enable CSRF protection if Flask-WTF is used
    if hasattr(app, "config"):
        app.config["WTF_CSRF_ENABLED"] = True
        app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hour
