# star_competency_app/utils/security_utils.py
import hashlib
import logging
import os
import secrets
from functools import wraps
from urllib.parse import urljoin, urlparse

from flask import current_app, request, session
from flask_login import current_user

logger = logging.getLogger(__name__)


def is_safe_url(target: str) -> bool:
    """
    Validate that a URL is safe to redirect to.

    Args:
        target: URL to validate

    Returns:
        True if the URL is safe, False otherwise
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def generate_secure_token() -> str:
    """
    Generate a cryptographically secure random token.

    Returns:
        Secure random token string
    """
    return secrets.token_hex(32)


def hash_password(password: str) -> str:
    """
    Hash a password securely (for demonstration, actual auth uses Azure SSO).

    Args:
        password: Password to hash

    Returns:
        Hashed password
    """
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        stored_password: Stored password hash
        provided_password: Password to check

    Returns:
        True if the password matches, False otherwise
    """
    salt_hex, key_hex = stored_password.split(":")
    salt = bytes.fromhex(salt_hex)
    stored_key = bytes.fromhex(key_hex)

    key = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100000)

    return key == stored_key


def require_api_key(view_function):
    """
    Decorator for API endpoints requiring an API key.
    """

    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != current_app.config.get("API_KEY"):
            logger.warning(f"Invalid API key attempt from {request.remote_addr}")
            return {"error": "Invalid or missing API key"}, 401
        return view_function(*args, **kwargs)

    return decorated_function


def require_admin(view_function):
    """
    Decorator for routes requiring admin privileges.
    """

    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            logger.warning(
                f"Unauthorized admin access attempt by user {current_user.id if current_user.is_authenticated else 'anonymous'}"
            )
            return {"error": "Admin privileges required"}, 403
        return view_function(*args, **kwargs)

    return decorated_function
