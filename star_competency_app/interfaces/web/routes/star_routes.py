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
    competencies = db_manager.get_competencies()

    if request.method == "POST":
        # Get form data
        title = request.form.get("title", "").strip()
        competency_id = request.form.get("competency_id")  # Raw input
        situation = request.form.get("situation", "")
        task = request.form.get("task", "")
        action = request.form.get("action", "")
        result = request.form.get("result", "")

        if not title:
            flash("Title is required", "error")
            return render_template("star/new.html", competencies=competencies)

        # Explicitly handle competency_id
        if not competency_id or competency_id.strip() == "":
            competency_id = None  # Set to None if empty
        else:
            try:
                competency_id = int(competency_id)
            except ValueError:
                logger.warning(f"Invalid competency_id received: {competency_id}")
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
    try:
        story = db_manager.get_star_story_by_id(story_id)
        if not story or story.user_id != current_user.id:
            logger.warning(
                f"Evaluate: story {story_id} not found or unauthorized user {current_user.id}"
            )
            return jsonify({"error": "STAR story not found"}), 404

        logger.info(f"Evaluating story {story_id} for user {current_user.id}")

        story_data = {
            "title": story.title,
            "situation": story.situation,
            "task": story.task,
            "action": story.action,
            "result": story.result,
        }

        result = prompt_agent.evaluate_star_story(
            story_data=story_data,
            competency_id=story.competency_id,
            user_id=current_user.id,
        )

        if "error" in result:
            logger.error(f"AI evaluation error for story {story_id}: {result['error']}")
            return jsonify({"error": result["error"]}), 500

        db_manager.update_star_story(
            story_id=story_id, ai_feedback=result.get("evaluation", "")
        )

        return jsonify(
            {
                "evaluation": result.get("evaluation", ""),
                "scores": result.get("scores", {}),
            }
        )

    except Exception as e:
        logger.exception(f"Unhandled exception during evaluation of story {story_id}")
        return jsonify({"error": f"Failed to evaluate STAR story: {str(e)}"}), 500


@star_bp.route("/<int:story_id>/improve", methods=["POST"])
@login_required
def improve_star_story(story_id):
    """Get improvement suggestions for a STAR story using AI."""
    story = db_manager.get_star_story_by_id(story_id)

    # Check if story exists and belongs to current user
    if not story or story.user_id != current_user.id:
        return jsonify({"error": "STAR story not found"}), 404

    # Call the proper method in prompt_agent
    result = prompt_agent.improve_star_story(story_id=story_id, user_id=current_user.id)

    if "error" in result:
        return jsonify({"error": result["error"]}), 500

    # Return the suggestions with proper response structure
    return jsonify(
        {
            "suggestions": result.get("evaluation", ""),
            "improved_components": result.get("improvement_suggestions", {}),
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


# @star_bp.route("/generate", methods=["POST"])
# @login_required
# def generate_star_structure():
#     """Generate STAR structure from a user's story using AI."""
#     # Get JSON data from request
#     data = request.json
#     if not data:
#         return jsonify({"error": "No data provided"}), 400

#     # Extract story content and competency ID
#     story_content = data.get("story_content", "")
#     competency_id = data.get("competency_id")

#     if not story_content.strip():
#         return jsonify({"error": "Story content is required"}), 400

#     try:
#         # Convert competency_id to int if not None
#         if competency_id:
#             try:
#                 competency_id = int(competency_id)
#             except ValueError:
#                 return jsonify({"error": "Invalid competency ID"}), 400
#         else:
#             # If no competency provided, we need to handle this differently
#             # OpenAIClient.generate_star_story expects a competency dict
#             # But PromptAgent.generate_star_story expects a competency_id

#             # Use the first competency in the system as a fallback
#             # or provide a special value to indicate a generic competency
#             competency_id = 1  # Assuming ID 1 exists, or handle appropriately

#         # Call prompt_agent.generate_star_story with the competency ID and context
#         result = prompt_agent.generate_star_story(
#             competency_id=competency_id, context=story_content, user_id=current_user.id
#         )

#         if "error" in result:
#             return jsonify({"error": result["error"]}), 500

#         # Return the generated STAR components
#         return jsonify(
#             {
#                 "situation": result.get("situation", ""),
#                 "task": result.get("task", ""),
#                 "action": result.get("action", ""),
#                 "result": result.get("result", ""),
#             }
#         )

#     except Exception as e:
#         logger.error(f"Error generating STAR structure: {str(e)}")
#         return jsonify({"error": f"Failed to generate STAR structure: {str(e)}"}), 500


@star_bp.route("/generate", methods=["POST"])
@login_required
def generate_star_structure():
    """Generate STAR structure from a user's story using AI."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    story_content = data.get("story_content", "")
    competency_id = data.get("competency_id")

    if not story_content.strip():
        return jsonify({"error": "Story content is required"}), 400

    try:
        if competency_id:
            try:
                competency_id = int(competency_id)
            except ValueError:
                return jsonify({"error": "Invalid competency ID"}), 400
        else:
            # Fallback competency ID (consider logging this too)
            competency_id = 1

        logger.info(
            f"Generating STAR structure for user_id={current_user.id}, competency_id={competency_id}"
        )

        result = prompt_agent.generate_star_story(
            competency_id=competency_id, context=story_content, user_id=current_user.id
        )

        if "error" in result:
            logger.error(f"STAR generation error: {result['error']}")
            return jsonify({"error": result["error"]}), 500

        return jsonify(
            {
                "situation": result.get("situation", ""),
                "task": result.get("task", ""),
                "action": result.get("action", ""),
                "result": result.get("result", ""),
            }
        )

    except Exception as e:
        logger.exception("Unhandled error during STAR generation")
        return jsonify({"error": f"Failed to generate STAR structure: {str(e)}"}), 500
