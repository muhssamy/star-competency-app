# star_competency_app/ai/openai_client.py
import base64
import json
import logging
from typing import Any, Dict, List, Optional

import openai

from star_competency_app.config.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.text_model = settings.OPENAI_TEXT_MODEL
        self.image_model = settings.OPENAI_IMAGE_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS

        # Initialize the client
        openai.api_key = self.api_key

    def analyze_text(
        self, text_content: str, competencies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Analyze text content using OpenAI text model.

        Args:
            text_content: Text to analyze
            competencies: List of competencies to align the analysis with

        Returns:
            Dict containing the analysis results
        """
        try:
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
            Analyze this content with focus on the following:
            
            1. Key issues and challenges presented
            2. Potential solutions and their pros/cons
            3. Recommended approach and implementation steps
            
            {competencies_context}
            
            Please be specific about which competencies are most relevant for addressing this and why.
            
            Content to analyze:
            {text_content}
            
            Provide your response in the following JSON format:
            {{
                "analysis": "Detailed analysis text here",
                "competency_alignment": {{
                    "CompetencyName1": {{"relevance": 0.9, "justification": "Why this competency is relevant"}},
                    "CompetencyName2": {{"relevance": 0.7, "justification": "Why this competency is relevant"}}
                }},
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }}
            """

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.text_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in analyzing business content and aligning it with competency frameworks.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                return {
                    "analysis": response.choices[0].message.content,
                    "competency_alignment": {},
                    "recommendations": [],
                }

        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {"error": str(e)}

    def analyze_image(
        self, image_path: str, competencies: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image using OpenAI vision model.

        Args:
            image_path: Path to the image file
            competencies: List of competencies to align the analysis with

        Returns:
            Dict containing the analysis results
        """
        try:
            # Read image file as base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

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
            Analyze this image with focus on extracting and understanding any text or diagrams visible.
            
            {competencies_context}
            
            Please be specific about which competencies are most relevant for addressing this and why.
            
            Provide your response in the following JSON format:
            {{
                "extracted_text": "Text visible in the image",
                "analysis": "Detailed analysis text here",
                "competency_alignment": {{
                    "CompetencyName1": {{"relevance": 0.9, "justification": "Why this competency is relevant"}},
                    "CompetencyName2": {{"relevance": 0.7, "justification": "Why this competency is relevant"}}
                }},
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }}
            """

            # Call OpenAI API with vision capabilities
            response = openai.ChatCompletion.create(
                model=self.image_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in analyzing visual content and aligning it with competency frameworks.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    },
                ],
                max_tokens=self.max_tokens,
                temperature=0.2,
            )

            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                return {
                    "extracted_text": "",
                    "analysis": response.choices[0].message.content,
                    "competency_alignment": {},
                    "recommendations": [],
                }

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {"error": str(e)}

    def evaluate_star_story(
        self, story: Dict[str, str], competency: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a STAR story using OpenAI.

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
            
            Provide your response in the following JSON format:
            {{
                "evaluation": "Detailed evaluation text here",
                "scores": {{
                    "completeness": 4.5,
                    "clarity": 3.8,
                    "relevance": 4.2,
                    "impact": 3.5,
                    "storytelling": 4.0,
                    "overall": 4.0
                }},
                "improvement_suggestions": {{
                    "situation": "Suggestion for improving the situation component",
                    "task": "Suggestion for improving the task component",
                    "action": "Suggestion for improving the action component",
                    "result": "Suggestion for improving the result component"
                }}
            }}
            """

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.text_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in evaluating STAR method stories and providing constructive feedback.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                return {
                    "evaluation": response.choices[0].message.content,
                    "scores": {
                        "completeness": 3.0,
                        "clarity": 3.0,
                        "relevance": 3.0,
                        "impact": 3.0,
                        "storytelling": 3.0,
                        "overall": 3.0,
                    },
                    "improvement_suggestions": {},
                }

        except Exception as e:
            logger.error(f"Error evaluating STAR story: {e}")
            return {"error": str(e)}

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
            
            Provide your response in the following JSON format:
            {{
                "title": "Title of the STAR story",
                "situation": "Detailed situation description",
                "task": "Detailed task description",
                "action": "Detailed action description",
                "result": "Detailed result description"
            }}
            """

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.text_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in creating compelling STAR method stories that demonstrate professional competencies.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                return {"error": "Failed to generate a properly structured STAR story"}

        except Exception as e:
            logger.error(f"Error generating STAR story: {e}")
            return {"error": str(e)}

    def perform_gap_analysis(
        self, user_stories: List[Dict], competencies: List[Dict]
    ) -> Dict[str, Any]:
        """
        Perform gap analysis on user's STAR stories against competency framework.

        Args:
            user_stories: List of user's STAR stories
            competencies: List of all competencies in the framework

        Returns:
            Dict containing gap analysis results
        """
        try:
            # Prepare stories context
            stories_context = "User's STAR Stories:\n"
            for i, story in enumerate(user_stories):
                stories_context += f"""
                Story {i+1}: {story.get('title', 'Untitled')}
                Competency: {story.get('competency_name', 'None')}
                Situation: {story.get('situation', 'Not provided')}
                Task: {story.get('task', 'Not provided')}
                Action: {story.get('action', 'Not provided')}
                Result: {story.get('result', 'Not provided')}
                
                """

            # Prepare competencies context
            competencies_context = "Competency Framework:\n"
            for comp in competencies:
                competencies_context += f"- {comp['name']}: {comp['description']}\n"

            # Prepare the prompt
            prompt = f"""
            Please perform a gap analysis between the user's STAR stories and the competency framework.
            
            {stories_context}
            
            {competencies_context}
            
            Analyze:
            1. Which competencies are well-covered by existing stories
            2. Which competencies are partially covered but need strengthening
            3. Which competencies are completely missing or inadequately demonstrated
            4. Suggestions for developing stories to fill the gaps
            
            Provide your response in the following JSON format:
            {{
                "summary": "Overall summary of the gap analysis",
                "covered_competencies": [
                    {{
                        "name": "Competency name",
                        "coverage_score": 0.9,
                        "assessment": "Assessment of how well this competency is covered"
                    }}
                ],
                "gap_competencies": [
                    {{
                        "name": "Competency name",
                        "coverage_score": 0.2,
                        "assessment": "Assessment of the gap",
                        "suggestions": ["Suggestion 1", "Suggestion 2"]
                    }}
                ],
                "recommended_priorities": ["Priority 1", "Priority 2", "Priority 3"]
            }}
            """

            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.text_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in competency frameworks and gap analysis.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Fallback if response is not valid JSON
                return {
                    "summary": response.choices[0].message.content,
                    "covered_competencies": [],
                    "gap_competencies": [],
                    "recommended_priorities": [],
                }

        except Exception as e:
            logger.error(f"Error performing gap analysis: {e}")
            return {"error": str(e)}
