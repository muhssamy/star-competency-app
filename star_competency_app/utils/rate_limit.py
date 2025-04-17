# star_competency_app/utils/rate_limit.py
import threading
import time
from functools import wraps

from flask import abort
from flask import current_app as app
from flask import g, request


# Simple in-memory rate limiter
class RateLimiter:
    def __init__(self, max_requests=100, period=60):
        self.max_requests = max_requests  # Maximum requests per period
        self.period = period  # Period in seconds
        self.requests = {}  # Dictionary to store request timestamps
        self.lock = threading.Lock()  # Thread lock for thread safety

    def is_rate_limited(self, key):
        """Check if a key is rate limited."""
        with self.lock:
            now = time.time()

            # Initialize or clean up expired timestamps
            if key not in self.requests:
                self.requests[key] = []

            # Remove timestamps older than the period
            self.requests[key] = [
                ts for ts in self.requests[key] if ts > now - self.period
            ]

            # Check if rate limit is reached
            if len(self.requests[key]) >= self.max_requests:
                return True

            # Add current timestamp
            self.requests[key].append(now)
            return False


# Create rate limiters for different endpoints
api_limiter = RateLimiter(max_requests=100, period=60)  # 100 requests per minute
ai_limiter = RateLimiter(max_requests=20, period=60)  # 20 AI requests per minute
auth_limiter = RateLimiter(max_requests=10, period=60)  # 10 auth attempts per minute


def rate_limit(limiter, key_func=None):
    """Decorator for rate limiting routes."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get the key to rate limit on
            if key_func:
                key = key_func()
            else:
                # Default to client IP
                key = request.remote_addr

            # Check if rate limited
            if limiter.is_rate_limited(key):
                abort(429)  # Too Many Requests

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Example usage:
# @app.route('/api/endpoint')
# @rate_limit(api_limiter)
# def api_endpoint():
#     return jsonify({"result": "success"})
