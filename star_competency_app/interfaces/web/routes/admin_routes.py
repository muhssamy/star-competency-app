# Create a new file: star_competency_app/interfaces/web/routes/admin_routes.py
import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from star_competency_app.database.db_manager import DatabaseManager
from star_competency_app.utils.security_utils import require_admin

logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint("admin", __name__)

# Initialize services
db_manager = DatabaseManager()


@admin_bp.route("/competencies")
@login_required
@require_admin
def manage_competencies():
    """Manage competencies."""
    competencies = db_manager.get_competencies()
    return render_template("admin/competencies.html", competencies=competencies)


@admin_bp.route("/competencies/new", methods=["POST"])
@login_required
@require_admin
def new_competency():
    """Create a new competency."""
    name = request.form.get("name", "")
    description = request.form.get("description", "")
    category = request.form.get("category", "")
    level = request.form.get("level", 1)

    if not name or not description:
        flash("Name and description are required", "error")
        return redirect(url_for("admin.manage_competencies"))

    # Create competency
    db_manager.create_competency(
        name=name, description=description, category=category, level=int(level)
    )

    flash("Competency created successfully", "success")
    return redirect(url_for("admin.manage_competencies"))


@admin_bp.route("/competencies/<int:competency_id>/edit", methods=["POST"])
@login_required
@require_admin
def edit_competency(competency_id):
    """Edit a competency."""
    name = request.form.get("name", "")
    description = request.form.get("description", "")
    category = request.form.get("category", "")
    level = request.form.get("level", 1)

    if not name or not description:
        flash("Name and description are required", "error")
        return redirect(url_for("admin.manage_competencies"))

    # Update competency
    db_manager.update_competency(
        competency_id=competency_id,
        name=name,
        description=description,
        category=category,
        level=int(level),
    )

    flash("Competency updated successfully", "success")
    return redirect(url_for("admin.manage_competencies"))


@admin_bp.route("/competencies/<int:competency_id>/delete", methods=["POST"])
@login_required
@require_admin
def delete_competency(competency_id):
    """Delete a competency."""
    # Check if competency is in use
    in_use = db_manager.is_competency_in_use(competency_id)

    if in_use:
        flash("Cannot delete competency that is in use", "error")
        return redirect(url_for("admin.manage_competencies"))

    # Delete competency
    db_manager.delete_competency(competency_id)

    flash("Competency deleted successfully", "success")
    return redirect(url_for("admin.manage_competencies"))


@admin_bp.route("/competency/<int:competency_id>/details")
def competency_details(competency_id):
    """Get competency details as JSON for AJAX requests."""
    competency = db_manager.get_competency_by_id(competency_id)

    if not competency:
        return jsonify({"error": "Competency not found"}), 404

    # Prepare response data
    data = {
        "id": competency.id,
        "name": competency.name,
        "description": competency.description,
        "category": competency.category,
        "level": competency.level,
        "expectations": competency.expectations,
    }

    return jsonify(data)


@admin_bp.route("/users")
@login_required
@require_admin
def manage_users():
    """Manage users."""
    users = db_manager.get_all_users()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@require_admin
def toggle_admin_role(user_id):
    """Toggle admin role for a user."""
    # Don't allow changing your own admin status
    if user_id == current_user.id:
        flash("You cannot change your own admin status.", "error")
        return redirect(url_for("admin.manage_users"))

    success = db_manager.toggle_admin_role(user_id)

    if success:
        flash("User admin status updated successfully.", "success")
    else:
        flash("Failed to update user admin status.", "error")

    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>/activity")
@login_required
@require_admin
def view_user_activity(user_id):
    """View activity for a specific user."""
    user = db_manager.get_user_by_id(user_id)

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.manage_users"))

    # Get user's activity logs
    activity_logs = db_manager.get_audit_logs_by_user(user_id)

    # Get user's STAR stories and case studies count
    star_stories_count = db_manager.count_star_stories_by_user(user_id)
    case_studies_count = db_manager.count_case_studies_by_user(user_id)

    return render_template(
        "admin/user_activity.html",
        user=user,
        activity_logs=activity_logs,
        star_stories_count=star_stories_count,
        case_studies_count=case_studies_count,
    )
