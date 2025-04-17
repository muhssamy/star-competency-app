# star_competency_app/interfaces/web/routes/auth_routes.py
import logging

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.orm.session import object_session

from star_competency_app.auth.azure_sso import AzureSSO
from star_competency_app.database.db_manager import DatabaseManager
from star_competency_app.utils.security_utils import is_safe_url

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint("auth", __name__)

# Initialize services
db_manager = DatabaseManager()
azure_sso = AzureSSO(db_manager=db_manager)


@auth_bp.route("/login")
def login():
    """Handle login requests."""
    # If user is already authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    # Generate Azure SSO login URL
    auth_url = azure_sso.get_auth_url()

    # Render login template with auth URL
    return render_template("auth/login.html", auth_url=auth_url)


@auth_bp.route("/callback")
def callback():
    """Handle Azure SSO callback."""
    # Process the login and get a properly detached user object
    success, user_info, error = azure_sso.process_login(request.args)

    if not success:
        flash(f"Login failed: {error}", "error")
        return redirect(url_for("auth.login"))

    # Get user ID from session data populated by process_login
    user_id = session["user"]["id"]

    # Get a fresh user object with proper detaching
    user = db_manager.get_user_by_id(user_id)

    if not user:
        flash("User account not found", "error")
        return redirect(url_for("auth.login"))

    # Login user with the detached but initialized user object
    login_user(user)

    # Redirect user
    next_page = session.get("next", None)
    if next_page and is_safe_url(next_page):
        return redirect(next_page)

    return redirect(url_for("dashboard"))


@auth_bp.route("/profile")
@login_required
def profile():
    """Display and manage user profile."""
    # Get user ID safely without triggering a database access
    user_id = int(current_user.get_id())

    # Get user's activity stats
    star_stories_count = db_manager.count_star_stories_by_user(user_id)
    case_studies_count = db_manager.count_case_studies_by_user(user_id)

    # Get user's recent activity
    recent_activity = db_manager.get_recent_audit_logs(user_id, limit=10)

    # Get user's competency coverage
    competencies = db_manager.get_competencies()
    coverage_stats = compute_competency_coverage(user_id, competencies)

    return render_template(
        "auth/profile.html",
        user=current_user,
        star_stories_count=star_stories_count,
        case_studies_count=case_studies_count,
        recent_activity=recent_activity,
        coverage_stats=coverage_stats,
    )


def compute_competency_coverage(user_id, all_competencies):
    """Compute competency coverage statistics for a user."""
    # Get user's STAR stories
    user_stories = db_manager.get_star_stories_by_user(user_id)

    # Count stories by competency
    covered_competencies = set()
    for story in user_stories:
        if story.competency_id:
            covered_competencies.add(story.competency_id)

    # Calculate coverage percentage
    total_competencies = len(all_competencies)
    covered_count = len(covered_competencies)
    coverage_percentage = (
        round((covered_count / total_competencies) * 100)
        if total_competencies > 0
        else 0
    )

    return {
        "total": total_competencies,
        "covered": covered_count,
        "percentage": coverage_percentage,
    }


@auth_bp.route("/logout")
@login_required
def logout():
    """Handle logout requests."""
    # Log out the user
    logout_user()

    # Get Azure logout URL
    logout_url = azure_sso.logout()

    # Clear session
    session.clear()

    # Redirect to Azure logout URL
    return redirect(logout_url)
