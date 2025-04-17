# star_competency_app/interfaces/web/app.py
import logging
import os
from datetime import datetime

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

FAVICON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),  # Path to `web/` directory
    "static",
    "favicon.ico",
)
from flask_login import LoginManager, current_user, login_required

from star_competency_app.ai.prompt_agent import PromptAgent
from star_competency_app.auth.azure_sso import AzureSSO
from star_competency_app.config.settings import get_settings
from star_competency_app.database.db_manager import DatabaseManager
from star_competency_app.database.seed import seed_competencies
from star_competency_app.interfaces.web.routes.admin_routes import admin_bp

# Import routes
from star_competency_app.interfaces.web.routes.auth_routes import auth_bp
from star_competency_app.interfaces.web.routes.case_study_routes import case_study_bp
from star_competency_app.interfaces.web.routes.gap_analysis_routes import (
    gap_analysis_bp,
)
from star_competency_app.interfaces.web.routes.star_routes import star_bp
from star_competency_app.utils.security_logging import setup_security_logging
from star_competency_app.utils.security_middleware import init_security
from star_competency_app.utils.security_utils import is_safe_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)

# Initialize security features
init_security(app)
setup_security_logging(app)

# Load application settings
settings = get_settings()
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Ensured upload directory exists: {settings.UPLOAD_FOLDER}")
app.config.update(
    SECRET_KEY=settings.SECRET_KEY,
    SESSION_COOKIE_SECURE=settings.SESSION_COOKIE_SECURE,
    SESSION_COOKIE_HTTPONLY=settings.SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE=settings.SESSION_COOKIE_SAMESITE,
    UPLOAD_FOLDER=settings.UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=settings.MAX_CONTENT_LENGTH,
)

# Initialize database
db_manager = DatabaseManager()
db_manager.create_tables()
seed_competencies(db_manager)
logger.info("Seeding competencies")

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

# Initialize Azure SSO
azure_sso = AzureSSO(db_manager=db_manager)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Initialize prompt agent
prompt_agent = PromptAgent(db_manager=db_manager)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(case_study_bp, url_prefix="/case-study")
app.register_blueprint(star_bp, url_prefix="/star")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(gap_analysis_bp, url_prefix="/gap-analysis")


@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login."""
    return db_manager.get_user_by_id(user_id)


@app.route("/")
def index():
    """Home page route."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page route."""
    # Get user's STAR stories
    star_stories = db_manager.get_star_stories_by_user(current_user.id)

    # Get user's case studies
    case_studies = db_manager.get_case_studies_by_user(current_user.id)

    # Get competencies
    competencies = db_manager.get_competencies()

    return render_template(
        "dashboard.html",
        star_stories=star_stories,
        case_studies=case_studies,
        competencies=competencies,
    )


@app.route("/favicon.ico")
def favicon():
    # Serve the favicon with hardcoded path
    return send_file(FAVICON_PATH, mimetype="image/vnd.microsoft.icon")


@app.route("/api/health")
def health_check():
    """API health check endpoint."""
    return jsonify({"status": "ok", "version": settings.APP_VERSION})


# star_competency_app/interfaces/web/app.py
# Add or update these error handlers in your app
@app.errorhandler(400)
def bad_request(e):
    """Handle 400 errors."""
    logger.error(f"400 error: {request.path} - {e}")
    return render_template("errors/400.html"), 400


@app.errorhandler(401)
def unauthorized(e):
    """Handle 401 errors."""
    logger.error(f"401 error: {request.path} - {e}")
    return render_template("errors/401.html"), 401


@app.errorhandler(403)
def forbidden(e):
    """Handle 403 errors."""
    logger.error(f"403 error: {request.path} - {e}")
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    logger.error(f"404 error: {request.path} - {e}")
    return render_template("errors/404.html"), 404


@app.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 errors."""
    logger.error(f"405 error: {request.path} - {e}")
    return render_template("errors/405.html"), 405


@app.errorhandler(429)
def too_many_requests(e):
    """Handle 429 errors (rate limiting)."""
    logger.error(f"429 error: {request.path} - {e}")
    return render_template("errors/429.html"), 429


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"500 error: {request.path} - {e}", exc_info=True)
    return render_template("errors/500.html"), 500


if __name__ == "__main__":
    # Create database tables if they don't exist
    db_manager.create_tables()

    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
