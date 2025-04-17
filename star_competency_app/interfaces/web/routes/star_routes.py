# star_competency_app/interfaces/web/routes/star_routes.py
import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from star_competency_app.ai.prompt_agent import PromptAgent
from star_competency_app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Create blueprint
star_bp = Blueprint("star", __name__)

# Initialize services
db_manager = DatabaseManager()
prompt_agent = PromptAgent(db_manager=db_manager)


@star_bp.route("/")
@login_required
def list_star_stories():
    """List all STAR stories for the current user."""
    star_stories = db_manager.get_star_stories_by_user(current_user.id)
    return render_template("star/list.html", star_stories=star_stories)


@star_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_star_story():
    """Create a new STAR story."""
    # Get competencies for dropdown
    competencies = db_manager.get_competencies()

    if request.method == "POST":
        # Get form data
        title = request.form.get("title", "")
        competency_id = request.form.get("competency_id")
        situation = request.form.get("situation", "")
        task = request.form.get("task", "")
        action = request.form.get("action", "")
        result = request.form.get("result", "")

        if not title:
            flash("Title is required", "error")
            return render_template("star/new.html", competencies=competencies)

        # Convert competency_id to int if not None
        if competency_id:
            try:
                competency_id = int(competency_id)
            except ValueError:
                competency_id = None

        # Create STAR story
        story = db_manager.create_star_story(
            user_id=current_user.id,
            title=title,
            competency_id=competency_id,
            situation=situation,
            task=task,
            action=action,
            result=result,
        )

        flash("STAR story created successfully", "success")
        return redirect(url_for("star.view_star_story", story_id=story.id))

    return render_template("star/new.html", competencies=competencies)


@star_bp.route("/<int:story_id>")
@login_required
def view_star_story(story_id):
    """View a specific STAR story."""
    story = db_manager.get_star_story_by_id(story_id)

    # Check if story exists and belongs to current user
    if not story or story.user_id != current_user.id:
        flash("STAR story not found", "error")
        return redirect(url_for("star.list_star_stories"))

    return render_template("star/view.html", story=story)


@star_bp.route("/<int:story_id>/edit", methods=["GET", "POST"])
@login_required
def edit_star_story(story_id):
    """Edit a STAR story."""
    story = db_manager.get_star_story_by_id(story_id)

    # Check if story exists and belongs to current user
    if not story or story.user_id != current_user.id:
        flash("STAR story not found", "error")
        return redirect(url_for("star.list_star_stories"))

    # Get competencies for dropdown
    competencies = db_manager.get_competencies()

    if request.method == "POST":
        # Get form data
        title = request.form.get("title", "")
        competency_id = request.form.get("competency_id")
        situation = request.form.get("situation", "")
        task = request.form.get("task", "")
        action = request.form.get("action", "")
        result = request.form.get("result", "")

        if not title:
            flash("Title is required", "error")
            return render_template(
                "star/edit.html", story=story, competencies=competencies
            )

        # Convert competency_id to int if not None
        if competency_id:
            try:
                competency_id = int(competency_id)
            except ValueError:
                competency_id = None

        # Update STAR story
        db_manager.update_star_story(
            story_id=story_id,
            title=title,
            competency_id=competency_id,
            situation=situation,
            task=task,
            action=action,
            result=result,
        )

        flash("STAR story updated successfully", "success")
        return redirect(url_for("star.view_star_story", story_id=story_id))

    return render_template("star/edit.html", story=story, competencies=competencies)


@star_bp.route("/<int:story_id>/evaluate", methods=["POST"])
@login_required
def evaluate_star_story(story_id):
    """Evaluate a STAR story using AI."""
    story = db_manager.get_star_story_by_id(story_id)

    # Check if story exists and belongs to current user
    if not story or story.user_id != current_user.id:
        return jsonify({"error": "STAR story not found"}), 404

    # Prepare story data
    story_data = {
        "title": story.title,
        "situation": story.situation,
        "task": story.task,
        "action": story.action,
        "result": story.result,
    }

    # Get competency if available
    competency = None
    if story.competency_id:
        competency = db_manager.get_competency_by_id(story.competency_id)

    # Evaluate story
    result = prompt_agent.optimize_star_story_prompt(
        user_query="Evaluate this STAR story",
        story_data=story_data,
        competency_id=story.competency_id,
        user_id=current_user.id,
    )

    if "error" in result:
        return jsonify({"error": result["error"]}), 500

    # Update story with AI feedback
    db_manager.update_star_story(
        story_id=story_id, ai_feedback=result.get("evaluation", "")
    )

    return jsonify(
        {"evaluation": result.get("evaluation", ""), "scores": result.get("scores", {})}
    )


@star_bp.route("/<int:story_id>/improve", methods=["POST"])
@login_required
def improve_star_story(story_id):
    """Get improvement suggestions for a STAR story using AI."""
    story = db_manager.get_star_story_by_id(story_id)

    # Check if story exists and belongs to current user
    if not story or story.user_id != current_user.id:
        return jsonify({"error": "STAR story not found"}), 404

    # Prepare story data
    story_data = {
        "title": story.title,
        "situation": story.situation,
        "task": story.task,
        "action": story.action,
        "result": story.result,
    }

    # Get improvement suggestions
    result = prompt_agent.optimize_star_story_prompt(
        user_query="Improve this STAR story",
        story_data=story_data,
        competency_id=story.competency_id,
        user_id=current_user.id,
    )

    if "error" in result:
        return jsonify({"error": result["error"]}), 500

    return jsonify(
        {
            "suggestions": result.get("suggestions", ""),
            "improved_components": result.get("improved_components", {}),
        }
    )


@star_bp.route("/<int:story_id>/delete", methods=["POST"])
@login_required
def delete_star_story(story_id):
    """Delete a STAR story."""
    story = db_manager.get_star_story_by_id(story_id)

    # Check if story exists and belongs to current user
    if not story or story.user_id != current_user.id:
        flash("STAR story not found", "error")
        return redirect(url_for("star.list_star_stories"))

    # Delete STAR story from database
    db_manager.delete_star_story(story_id)

    flash("STAR story deleted successfully", "success")
    return redirect(url_for("star.list_star_stories"))
