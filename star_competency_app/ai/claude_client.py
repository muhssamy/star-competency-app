# star_competency_app/ai/claude_client.py
import logging
import re
from typing import Any, Dict, List, Optional

import anthropic
from anthropic.types import Message

from star_competency_app.config.settings import get_settings
from star_competency_app.utils.text_utils import extract_text_from_image

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.CLAUDE_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.max_tokens = settings.CLAUDE_MAX_TOKENS

    def analyze_case_study(
        self,
        image_path: Optional[str] = None,
        text_content: Optional[str] = None,
        competencies: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a case study using Claude API.

        Args:
            image_path: Path to the case study image
            text_content: Text content of the case study
            competencies: List of competencies to align the analysis with

        Returns:
            Dict containing the analysis results
        """
        try:
            # Extract text from image if provided
            if image_path and not text_content:
                text_content = extract_text_from_image(image_path)

            if not text_content:
                return {"error": "No content provided for analysis"}

            # Prepare competencies context
            competencies_context = ""
            if competencies:
                competencies_context = (
                    "Consider the following competencies in your analysis:\n"
                )
                for comp in competencies:
                    competencies_context += f"- {comp['name']}: {comp['description']}\n"

            # Prepare the prompt
            prompt = f"""
            You are analyzing a business case study. Please provide a comprehensive analysis with a focus on the following:
            
            1. Key issues and challenges presented in the case
            2. Stakeholders involved and their interests
            3. Potential solutions and their pros/cons
            4. Recommended approach and implementation steps
            
            {competencies_context}
            
            Please be specific about which competencies are most relevant for addressing this case and why.
            
            Here is the case study:
            {text_content}
            """

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "analysis": response.content[0].text,
                "competency_alignment": self._extract_competency_alignment(
                    response.content[0].text, competencies
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing case study: {e}")
            return {"error": str(e)}

    def evaluate_star_story(
        self, story: Dict[str, str], competency: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a STAR story using Claude API.

        Args:
            story: Dict containing situation, task, action, result
            competency: The competency this story is meant to demonstrate

        Returns:
            Dict containing the evaluation results
        """
        try:
            # Prepare competency context
            competency_context = ""
            if competency:
                competency_context = f"""
                This STAR story is meant to demonstrate the competency:
                "{competency['name']}: {competency['description']}"
                """

            # Prepare the prompt
            prompt = f"""
            Please evaluate this STAR (Situation, Task, Action, Result) story and provide feedback on:
            
            1. Completeness and clarity of each STAR component
            2. Effectiveness in demonstrating the relevant skills and behaviors
            3. Impact and measurability of the results
            4. Overall storytelling and persuasiveness
            5. Areas for improvement
            
            {competency_context}
            
            STAR Story:
            Title: {story.get('title', 'No title provided')}
            
            Situation: {story.get('situation', 'Not provided')}
            
            Task: {story.get('task', 'Not provided')}
            
            Action: {story.get('action', 'Not provided')}
            
            Result: {story.get('result', 'Not provided')}
            """

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "evaluation": response.content[0].text,
                "scores": self._extract_evaluation_scores(response.content[0].text),
            }

        except Exception as e:
            logger.error(f"Error evaluating STAR story: {e}")
            return {"error": str(e)}

    def suggest_star_improvements(
        self, story: Dict[str, str], competency: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Suggest improvements for a STAR story using Claude API.

        Args:
            story: Dict containing situation, task, action, result
            competency: The competency this story is meant to demonstrate

        Returns:
            Dict containing suggested improvements
        """
        try:
            # Prepare competency context
            competency_context = ""
            if competency:
                competency_context = f"""
                This STAR story is meant to demonstrate the competency:
                "{competency['name']}: {competency['description']}"
                Please ensure your suggestions help align the story better with this competency.
                """

            # Prepare the prompt
            prompt = f"""
            Please suggest specific improvements for each component of this STAR (Situation, Task, Action, Result) story.
            Focus on making the story more compelling, specific, and effective for demonstrating skills in a professional context.
            
            {competency_context}
            
            STAR Story:
            Title: {story.get('title', 'No title provided')}
            
            Situation: {story.get('situation', 'Not provided')}
            
            Task: {story.get('task', 'Not provided')}
            
            Action: {story.get('action', 'Not provided')}
            
            Result: {story.get('result', 'Not provided')}
            
            For each component (Situation, Task, Action, Result), please provide:
            1. Specific suggestions for improvement
            2. Example text showing how it could be rewritten
            
            Structure your response with clear headers for each STAR component and separate the suggestions from the examples.
            """

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "suggestions": response.content[0].text,
                "improved_components": self._extract_improved_components(
                    response.content[0].text, story
                ),
            }

        except Exception as e:
            logger.error(f"Error suggesting STAR improvements: {e}")
            return {"error": str(e)}

    def _extract_competency_alignment(
        self, analysis_text: str, competencies: Optional[List[Dict]]
    ) -> Dict:
        """Extract competency alignment from analysis text."""
        if not competencies:
            return {}

        alignment = {}
        for comp in competencies:
            name = comp["name"]
            # Simple heuristic - count mentions of the competency
            mentions = analysis_text.lower().count(name.lower())
            if mentions > 0:
                alignment[name] = {
                    "mentions": mentions,
                    "relevant": mentions > 1,  # Simple relevance heuristic
                }

        return alignment

    def _extract_evaluation_scores(self, evaluation_text: str) -> Dict:
        """Extract numeric scores from evaluation text (heuristic-based)."""
        categories = {
            "completeness": ["complete", "comprehensive", "thorough"],
            "clarity": ["clear", "specific", "detail"],
            "relevance": ["relevant", "aligned", "demonstrate"],
            "impact": ["impact", "result", "outcome", "measure"],
            "storytelling": ["compelling", "persuasive", "engaging"],
        }

        scores = {}
        for category, keywords in categories.items():
            # Simple scoring heuristic based on positive/negative keywords
            score = 3  # Default neutral score

            # Look for positive indicators
            positives = ["excellent", "great", "very good", "strong", "well"]
            for word in positives:
                for keyword in keywords:
                    if f"{word} {keyword}" in evaluation_text.lower():
                        score += 1
                        break

            # Look for negative indicators
            negatives = [
                "lacking",
                "missing",
                "weak",
                "insufficient",
                "could be better",
            ]
            for word in negatives:
                for keyword in keywords:
                    if f"{word} {keyword}" in evaluation_text.lower():
                        score -= 1
                        break

            # Normalize to 1-5 range
            scores[category] = max(1, min(5, score))

        # Calculate overall score
        scores["overall"] = round(sum(scores.values()) / len(scores), 1)

        return scores

    def _extract_improved_components(
        self, suggestions_text: str, original_story: Dict[str, str]
    ) -> Dict:
        """Extract improved components from suggestions text."""
        components = ["situation", "task", "action", "result"]
        improved = {}

        for component in components:
            # Try to find example text for each component
            # Look for patterns like "Example:" or "Rewritten:" followed by text
            component_lower = component.lower()

            # Define regex patterns to find improved text sections
            patterns = [
                rf"{component}.*?Example[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
                rf"{component}.*?Rewritten[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
                rf"{component}.*?Improved[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
                rf"{component}.*?Could be[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)",
            ]

            # Try each pattern
            for pattern in patterns:
                match = re.search(pattern, suggestions_text, re.IGNORECASE | re.DOTALL)
                if match:
                    improved_text = match.group(1).strip()
                    improved[component] = improved_text
                    break

            # If no match found, keep the original
            if component not in improved and component in original_story:
                improved[component] = original_story[component]

        return improved

    def generate_star_story(
        self, competency: Dict, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a new STAR story based on a competency.

        Args:
            competency: The competency to create a story for
            context: Optional context or work experience to include

        Returns:
            Dict containing the generated STAR story
        """
        try:
            # Prepare context
            context_prompt = ""
            if context:
                context_prompt = f"""
                Use this context/experience when creating the story:
                {context}
                """

            # Prepare the prompt
            prompt = f"""
            Please generate a high-quality STAR (Situation, Task, Action, Result) story that demonstrates the following competency:
            
            Competency: {competency['name']}
            Description: {competency['description']}
            
            {context_prompt}
            
            The story should:
            1. Be specific and detailed
            2. Clearly demonstrate the competency
            3. Show measurable results
            4. Be structured in the STAR format
            5. Be written in first person
            
            Please structure your response with clear headers for Title, Situation, Task, Action, and Result.
            """

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse the response to extract STAR components
            story_text = response.content[0].text
            story_components = self._extract_story_components(story_text)

            return {"generated_story": story_text, "components": story_components}

        except Exception as e:
            logger.error(f"Error generating STAR story: {e}")
            return {"error": str(e)}

    def _extract_story_components(self, story_text: str) -> Dict[str, str]:
        """Extract STAR components from generated story text."""
        components = {
            "title": "",
            "situation": "",
            "task": "",
            "action": "",
            "result": "",
        }

        # Extract title
        title_match = re.search(
            r"(?:Title|#\s*Title)[:\s]+(.*?)(?=\n\n|\n#|\n\*\*|$)",
            story_text,
            re.IGNORECASE | re.DOTALL,
        )
        if title_match:
            components["title"] = title_match.group(1).strip()

        # Extract each component
        for component in ["situation", "task", "action", "result"]:
            component_match = re.search(
                rf"(?:{component}|#\s*{component})[:\s]+(.*?)(?=\n\n(?:\w+:|#|\*\*)|$)",
                story_text,
                re.IGNORECASE | re.DOTALL,
            )
            if component_match:
                components[component] = component_match.group(1).strip()

        return components

    def create_prompt_agent(
        self,
        user_query: str,
        competencies: Optional[List[Dict]] = None,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Create an optimized prompt using the AI agent.

        Args:
            user_query: The user's original query
            competencies: Available competencies for context
            context: Additional context like previous interactions

        Returns:
            Dict containing the optimized prompt
        """
        try:
            # Prepare competencies context
            competencies_context = ""
            if competencies:
                competencies_context = "Consider the following competencies:\n"
                for comp in competencies:
                    competencies_context += f"- {comp['name']}: {comp['description']}\n"

            # Prepare additional context
            additional_context = ""
            if context:
                if "previous_queries" in context:
                    additional_context += (
                        f"Previous queries: {context['previous_queries']}\n"
                    )
                if "user_role" in context:
                    additional_context += f"User role: {context['user_role']}\n"

            # Prepare the prompt
            prompt = f"""
            You are a prompt engineering expert. Your task is to transform this user query into an optimized prompt for Claude to generate the best possible response.
            
            The original query is about a competency framework and STAR method stories. The user is likely preparing for a performance review or promotion.
            
            {competencies_context}
            
            {additional_context}
            
            Original user query:
            "{user_query}"
            
            Please create an optimized prompt that:
            1. Adds necessary structure and context
            2. Makes the request more specific
            3. Aligns with the competency framework
            4. Follows best practices for prompting Claude
            5. Maintains the user's original intent
            
            Return ONLY the optimized prompt with no explanations or metadata.
            """

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            optimized_prompt = response.content[0].text

            return {"original_query": user_query, "optimized_prompt": optimized_prompt}

        except Exception as e:
            logger.error(f"Error creating optimized prompt: {e}")
            return {
                "original_query": user_query,
                "optimized_prompt": user_query,  # Fallback to original query
                "error": str(e),
            }
