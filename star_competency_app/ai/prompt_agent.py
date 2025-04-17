# star_competency_app/ai/prompt_agent.py
import logging
import os
from typing import Any, Dict, List, Optional

from star_competency_app.ai.openai_client import OpenAIClient
from star_competency_app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PromptAgent:
    """
    AI agent that optimizes prompts between the user and OpenAI API.
    Acts as an intermediary to improve prompt quality and response relevance.
    """

    def __init__(
        self,
        openai_client: Optional[OpenAIClient] = None,
        db_manager: Optional[DatabaseManager] = None,
    ):
        # Use environment variable to get the API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # If no client is provided, create one with the API key from environment
        self.openai_client = openai_client or OpenAIClient(api_key=api_key)

        # Rest of the initialization remains the same
        self.db_manager = db_manager or DatabaseManager()
        self.context = {}

    def analyze_case_study(
        self,
        image_path: Optional[str] = None,
        text_content: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a case study using the appropriate OpenAI model based on input type.

        Args:
            image_path: Path to the case study image
            text_content: Text content of the case study
            user_id: User ID for personalization

        Returns:
            Dict containing the analysis results
        """
        try:
            # Get relevant competencies
            competencies = self.db_manager.get_competencies()

            # Get user context if user_id provided
            user_context = None
            if user_id:
                user = self.db_manager.get_user_by_id(user_id)
                if user:
                    user_context = {"user_role": user.display_name}

                    # Get user's recent STAR stories for context
                    recent_stories = self.db_manager.get_recent_star_stories_by_user(
                        user_id, limit=3
                    )
                    if recent_stories:
                        user_context["recent_stories"] = recent_stories

            # Choose appropriate analysis method based on input
            if image_path:
                analysis_result = self.openai_client.analyze_image(
                    image_path=image_path, competencies=competencies
                )

                # Log this analysis
                if user_id:
                    self.db_manager.log_audit(
                        user_id=user_id,
                        action="image_analysis",
                        entity_type="case_study",
                        details=f"Image analysis for {image_path}",
                    )
            elif text_content:
                analysis_result = self.openai_client.analyze_text(
                    text_content=text_content, competencies=competencies
                )

                # Log this analysis
                if user_id:
                    self.db_manager.log_audit(
                        user_id=user_id,
                        action="text_analysis",
                        entity_type="case_study",
                        details=f"Text analysis: {text_content[:100]}...",
                    )
            else:
                return {"error": "No content provided for analysis"}

            # Return analysis result
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing case study: {e}")
            return {"error": str(e)}

    def evaluate_star_story(
        self,
        story_data: Dict[str, str],
        competency_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a STAR story.

        Args:
            story_data: Dictionary containing STAR story components
            competency_id: ID of the specific competency
            user_id: User ID for personalization

        Returns:
            Dict containing the evaluation results
        """
        try:
            # Get competency if ID provided
            competency = None
            if competency_id:
                competency = self.db_manager.get_competency_by_id(competency_id)

            # Evaluate the story
            evaluation_result = self.openai_client.evaluate_star_story(
                story_data=story_data, competency=competency
            )

            # Log this evaluation
            if user_id:
                self.db_manager.log_audit(
                    user_id=user_id,
                    action="evaluate_story",
                    entity_type="star_story",
                    details=f"Evaluated story: {story_data.get('title', 'Untitled')}",
                )

            return evaluation_result

        except Exception as e:
            logger.error(f"Error evaluating STAR story: {e}")
            return {"error": str(e)}

    def generate_star_story(
        self,
        competency_id: int,
        context: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a STAR story for a specific competency.

        Args:
            competency_id: ID of the competency to generate a story for
            context: Optional context for story generation
            user_id: User ID for personalization

        Returns:
            Dict containing the generated story or an error message
        """
        try:
            # Get competency details from the database
            competency = self.db_manager.get_competency_by_id(competency_id)
            if not competency:
                logger.warning(f"Competency with ID {competency_id} not found.")
                return {"error": "Competency not found"}

            logger.info(
                f"Generating STAR story for competency: {competency.name}, user_id={user_id}"
            )

            # Call the OpenAI client to generate the story
            story_result = self.openai_client.generate_star_story(
                competency=competency, context=context
            )

            logger.debug(f"OpenAI story result: {story_result}")

            # Log the generation in audit trail
            if user_id:
                self.db_manager.log_audit(
                    user_id=user_id,
                    action="generate_story",
                    entity_type="star_story",
                    details=f"Generated story for competency: {competency.name}",
                )

            return story_result

        except Exception as e:
            logger.exception("Failed to generate STAR story")
            return {"error": f"OpenAI generation failed: {str(e)}"}

    def perform_gap_analysis(self, user_id: int) -> Dict[str, Any]:
        """
        Perform a gap analysis for a user's STAR stories against the competency framework.

        Args:
            user_id: User ID

        Returns:
            Dict containing the gap analysis results
        """
        try:
            # Get user's STAR stories
            user_stories = self.db_manager.get_star_stories_by_user(user_id)
            if not user_stories:
                return {
                    "error": "No STAR stories found for this user",
                    "recommendation": "Create some STAR stories first to perform a gap analysis",
                }

            # Get all competencies
            competencies = self.db_manager.get_competencies()
            if not competencies:
                return {"error": "No competencies found in the system"}

            # Format stories for gap analysis
            formatted_stories = []
            for story in user_stories:
                competency_name = (
                    story.competency.name if story.competency else "No competency"
                )
                formatted_stories.append(
                    {
                        "title": story.title,
                        "competency_name": competency_name,
                        "situation": story.situation,
                        "task": story.task,
                        "action": story.action,
                        "result": story.result,
                    }
                )

            # Format competencies for gap analysis
            formatted_competencies = []
            for comp in competencies:
                formatted_competencies.append(
                    {
                        "id": comp.id,
                        "name": comp.name,
                        "description": comp.description,
                        "category": comp.category,
                    }
                )

            # Perform gap analysis
            gap_analysis = self.openai_client.perform_gap_analysis(
                user_stories=formatted_stories, competencies=formatted_competencies
            )

            # Log this analysis
            self.db_manager.log_audit(
                user_id=user_id,
                action="gap_analysis",
                entity_type="user",
                details=f"Performed gap analysis across {len(user_stories)} stories and {len(competencies)} competencies",
            )

            return gap_analysis

        except Exception as e:
            logger.error(f"Error performing gap analysis: {e}")
            return {"error": str(e)}

    def improve_star_story(
        self, story_id: int, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get improvement suggestions for a STAR story.

        Args:
            story_id: ID of the STAR story to improve
            user_id: User ID for verification

        Returns:
            Dict containing improvement suggestions
        """
        try:
            # Get the story
            story = self.db_manager.get_star_story_by_id(story_id)
            if not story:
                return {"error": "STAR story not found"}

            # Verify ownership if user_id provided
            if user_id and story.user_id != user_id:
                return {"error": "Not authorized to access this STAR story"}

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
                competency = self.db_manager.get_competency_by_id(story.competency_id)

            # Evaluate the story to get improvement suggestions
            evaluation_result = self.openai_client.evaluate_star_story(
                story=story_data, competency=competency
            )

            # Extract improvement suggestions
            if "improvement_suggestions" in evaluation_result:
                result = {
                    "original_story": story_data,
                    "improvement_suggestions": evaluation_result[
                        "improvement_suggestions"
                    ],
                    "evaluation": evaluation_result.get("evaluation", ""),
                }
            else:
                result = {
                    "original_story": story_data,
                    "improvement_suggestions": {},
                    "evaluation": evaluation_result.get("evaluation", ""),
                }

            # Log this improvement request
            if user_id:
                self.db_manager.log_audit(
                    user_id=user_id,
                    action="improve_story",
                    entity_type="star_story",
                    entity_id=story_id,
                    details=f"Requested improvements for story: {story.title}",
                )

            return result

        except Exception as e:
            logger.error(f"Error improving STAR story: {e}")
            return {"error": str(e)}

    def handle_general_query(
        self, user_query: str, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Handle a general query about competencies or STAR method.

        Args:
            user_query: Original query from the user
            user_id: User ID for personalization

        Returns:
            Dict containing the response
        """
        try:
            # Get competencies for context
            competencies = self.db_manager.get_competencies()

            # Create competencies context
            competencies_context = "Consider the following competencies:\n"
            for comp in competencies:
                competencies_context += f"- {comp.name}: {comp.description}\n"

            # Prepare the prompt
            prompt = f"""
            Please answer this query about competencies or the STAR method:
            
            {competencies_context}
            
            User query: {user_query}
            
            Provide a helpful, informative response that directly addresses the query.
            """

            # Use analyze_text for handling general queries
            response = self.openai_client.analyze_text(text_content=prompt)

            # Log this query
            if user_id:
                self.db_manager.log_audit(
                    user_id=user_id,
                    action="general_query",
                    entity_type="user",
                    details=user_query,
                )

            # Extract just the analysis part for general queries
            if "analysis" in response:
                return {"response": response["analysis"]}
            else:
                return {
                    "response": "I'm sorry, I couldn't generate a proper response to your query."
                }

        except Exception as e:
            logger.error(f"Error handling general query: {e}")
            return {"error": str(e)}
