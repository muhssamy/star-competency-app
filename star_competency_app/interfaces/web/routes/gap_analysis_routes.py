# star_competency_app/interfaces/web/routes/gap_analysis_routes.py
import logging

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required

from star_competency_app.ai.prompt_agent import PromptAgent
from star_competency_app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Create blueprint
gap_analysis_bp = Blueprint("gap_analysis", __name__)

# Initialize services
db_manager = DatabaseManager()
prompt_agent = PromptAgent(db_manager=db_manager)


@gap_analysis_bp.route("/")
@login_required
def view_gap_analysis():
    """Display the gap analysis dashboard."""
    # Get user's STAR stories
    star_stories = db_manager.get_star_stories_by_user(current_user.id)

    # Get all competencies
    competencies = db_manager.get_competencies()

    # Check if user has any stories
    if not star_stories:
        flash(
            "You need to create some STAR stories before performing a gap analysis.",
            "warning",
        )
        return render_template(
            "gap_analysis/no_stories.html", competencies=competencies
        )

    # Get coverage statistics
    coverage_stats = compute_coverage_stats(star_stories, competencies)

    return render_template(
        "gap_analysis/dashboard.html",
        star_stories=star_stories,
        competencies=competencies,
        coverage_stats=coverage_stats,
    )


@gap_analysis_bp.route("/analyze", methods=["POST"])
@login_required
def run_gap_analysis():
    """Run the AI gap analysis."""
    # Call the prompt agent to perform gap analysis
    analysis_result = prompt_agent.perform_gap_analysis(user_id=current_user.id)

    if "error" in analysis_result:
        flash(f"Error performing gap analysis: {analysis_result['error']}", "error")
        return redirect(url_for("gap_analysis.view_gap_analysis"))

    # Store the analysis result in session for rendering
    session["gap_analysis_result"] = analysis_result

    return redirect(url_for("gap_analysis.view_analysis_results"))


@gap_analysis_bp.route("/results")
@login_required
def view_analysis_results():
    """Display the gap analysis results."""
    # Get analysis result from session
    analysis_result = session.get("gap_analysis_result")

    if not analysis_result:
        flash("No analysis results found. Please run a gap analysis first.", "warning")
        return redirect(url_for("gap_analysis.view_gap_analysis"))

    # Get all competencies for reference
    competencies = db_manager.get_competencies()

    return render_template(
        "gap_analysis/results.html",
        analysis_result=analysis_result,
        competencies=competencies,
    )


def compute_coverage_stats(stories, competencies):
    """
    Compute basic coverage statistics without using AI.

    Args:
        stories: List of user's STAR stories
        competencies: List of all competencies

    Returns:
        Dict containing coverage statistics
    """
    # Create a dictionary to store coverage by competency
    coverage = {}

    # Count stories by competency
    for comp in competencies:
        coverage[comp.id] = {
            "id": comp.id,
            "name": comp.name,
            "category": comp.category,
            "story_count": 0,
            "stories": [],
        }

    # Count stories for each competency
    for story in stories:
        if story.competency_id and story.competency_id in coverage:
            coverage[story.competency_id]["story_count"] += 1
            coverage[story.competency_id]["stories"].append(
                {"id": story.id, "title": story.title}
            )

    # Calculate overall statistics
    total_competencies = len(competencies)
    covered_competencies = len([c for c in coverage.values() if c["story_count"] > 0])
    coverage_percentage = (
        round((covered_competencies / total_competencies) * 100)
        if total_competencies > 0
        else 0
    )

    return {
        "competencies": coverage,
        "total_competencies": total_competencies,
        "covered_competencies": covered_competencies,
        "coverage_percentage": coverage_percentage,
    }
