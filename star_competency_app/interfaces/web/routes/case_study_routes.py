# star_competency_app/interfaces/web/routes/case_study_routes.py
import logging
import os

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from star_competency_app.ai.prompt_agent import PromptAgent
from star_competency_app.database.db_manager import DatabaseManager
from star_competency_app.utils.image_utils import (
    extract_text_from_image,
    save_uploaded_image,
)

logger = logging.getLogger(__name__)

# Create blueprint
case_study_bp = Blueprint("case_study", __name__)

# Initialize services
db_manager = DatabaseManager()
prompt_agent = PromptAgent(db_manager=db_manager)


@case_study_bp.route("/")
@login_required
def list_case_studies():
    """List all case studies for the current user."""
    case_studies = db_manager.get_case_studies_by_user(current_user.id)
    return render_template("case_study/list.html", case_studies=case_studies)


@case_study_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_case_study():
    """Create a new case study."""
    if request.method == "POST":
        # Get form data
        title = request.form.get("title", "")
        description = request.form.get("description", "")

        if not title:
            flash("Title is required", "error")
            return render_template("case_study/new.html")

        # Handle file upload
        file = request.files.get("case_study_image")
        image_path = None

        if file:
            image_path = save_uploaded_image(file, current_user.id)

            if not image_path:
                flash("Failed to save image", "error")
                return render_template("case_study/new.html")

        # Create case study
        case_study = db_manager.create_case_study(
            user_id=current_user.id,
            title=title,
            description=description,
            image_path=image_path,
        )

        flash("Case study created successfully", "success")
        return redirect(url_for("case_study.view_case_study", case_id=case_study.id))

    return render_template("case_study/new.html")


@case_study_bp.route("/<int:case_id>")
@login_required
def view_case_study(case_id):
    """View a specific case study."""
    case_study = db_manager.get_case_study_by_id(case_id)

    # Check if case study exists and belongs to current user
    if not case_study or case_study.user_id != current_user.id:
        flash("Case study not found", "error")
        return redirect(url_for("case_study.list_case_studies"))

    # Get competencies
    competencies = db_manager.get_competencies()

    return render_template(
        "case_study/view.html", case_study=case_study, competencies=competencies
    )


@case_study_bp.route("/<int:case_id>/analyze", methods=["POST"])
@login_required
def analyze_case_study(case_id):
    """Analyze a case study using AI."""
    case_study = db_manager.get_case_study_by_id(case_id)

    # Check if case study exists and belongs to current user
    if not case_study or case_study.user_id != current_user.id:
        return jsonify({"error": "Case study not found"}), 404

    # Get query from request
    query = request.form.get("query", "Analyze this case study")

    # Analyze case study
    result = prompt_agent.optimize_case_study_prompt(
        user_query=query, image_path=case_study.image_path, user_id=current_user.id
    )

    if "error" in result:
        return jsonify({"error": result["error"]}), 500

    # Update case study with analysis
    db_manager.update_case_study(
        case_id=case_id, claude_analysis=result.get("analysis", "")
    )

    return jsonify(
        {
            "analysis": result.get("analysis", ""),
            "competency_alignment": result.get("competency_alignment", {}),
        }
    )


@case_study_bp.route("/<int:case_id>/delete", methods=["POST"])
@login_required
def delete_case_study(case_id):
    """Delete a case study."""
    case_study = db_manager.get_case_study_by_id(case_id)

    # Check if case study exists and belongs to current user
    if not case_study or case_study.user_id != current_user.id:
        flash("Case study not found", "error")
        return redirect(url_for("case_study.list_case_studies"))

    # Delete image file if exists
    if case_study.image_path and os.path.exists(case_study.image_path):
        try:
            os.remove(case_study.image_path)
        except Exception as e:
            logger.error(f"Failed to delete image file: {e}")

    # Delete case study from database
    db_manager.delete_case_study(case_id)

    flash("Case study deleted successfully", "success")
    return redirect(url_for("case_study.list_case_studies"))
