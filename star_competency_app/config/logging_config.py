# star_competency_app/config/logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


def configure_logging(app):
    """Configure application logging."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    # Configure main application logger
    app_logger = logging.getLogger("star_competency_app")
    app_logger.setLevel(logging.INFO)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File handler for general logs - rotate when size reaches 5MB, keep 10 backup files
    app_log_path = os.path.join(logs_dir, "app.log")
    file_handler = RotatingFileHandler(
        app_log_path, maxBytes=5 * 1024 * 1024, backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Error file handler - only ERROR and above
    error_log_path = os.path.join(logs_dir, "error.log")
    error_handler = RotatingFileHandler(
        error_log_path, maxBytes=5 * 1024 * 1024, backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)

    # Security logger - daily rotation, keep 30 days of logs
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.INFO)
    security_log_path = os.path.join(logs_dir, "security.log")
    security_handler = TimedRotatingFileHandler(
        security_log_path, when="midnight", interval=1, backupCount=30
    )
    security_formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(message)s"
    )
    security_handler.setFormatter(security_formatter)
    security_logger.addHandler(security_handler)

    # Add handlers to app logger
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(error_handler)

    # Configure Flask's logger to use our settings
    flask_logger = logging.getLogger("flask.app")
    for handler in flask_logger.handlers:
        flask_logger.removeHandler(handler)
    flask_logger.setLevel(logging.INFO)
    flask_logger.addHandler(console_handler)
    flask_logger.addHandler(file_handler)
    flask_logger.addHandler(error_handler)

    # Add error log handler to SQLAlchemy logger
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.addHandler(error_handler)

    # Disable propagation for security logger
    security_logger.propagate = False

    return app_logger
