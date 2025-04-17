# star_competency_app/ai/openai_client.py
import logging
from typing import Any, Dict

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_star_story(self, competency: Any, context: str) -> Dict[str, Any]:
        """
        Generate a STAR story given a competency ORM object and a context string.
        """
        try:
            # Extract ORM attributes directly
            name = competency.name
            description = getattr(competency, "description", "") or ""

            # Build the prompt
            prompt = (
                f"Generate a STAR story for competency '{name}'.\n"
                f"Description: {description}\n"
                f"Context: {context}\n"
                "Provide clear sections labeled Situation, Task, Action, and Result."
            )

            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            text = response.choices[0].message.content
            story = self._parse_star_response(text)
            return story

        except Exception as e:
            logger.exception(f"Error generating STAR story: {e}")
            return {"error": str(e)}

    def evaluate_star_story(
        self, story_data: Dict[str, Any], competency: Any
    ) -> Dict[str, Any]:
        """
        Evaluate an existing STAR story against a competency ORM object.
        """
        try:
            name = competency.name

            prompt = (
                f"Evaluate the following STAR story against the competency '{name}'.\n"
                f"Situation: {story_data['situation']}\n"
                f"Task: {story_data['task']}\n"
                f"Action: {story_data['action']}\n"
                f"Result: {story_data['result']}\n"
                "Provide constructive feedback and assign a score out of 5."
            )

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=300,
            )

            text = response.choices[0].message.content
            evaluation, scores = self._parse_evaluation_response(text)
            return {"evaluation": evaluation, "scores": scores}

        except Exception as e:
            logger.exception(f"Error evaluating STAR story: {e}")
            return {"error": str(e)}

    def _parse_star_response(self, text: str) -> Dict[str, str]:
        parts = {"situation": "", "task": "", "action": "", "result": ""}

        # Try to split the text into sections using bold markers
        sections = text.split("**")

        # Mapping of section keywords
        section_map = {
            "situation": "situation",
            "task": "task",
            "action": "action",
            "result": "result",
        }

        # Process each section
        for i in range(1, len(sections), 2):
            section_header = sections[i].lower().strip(":")
            section_content = sections[i + 1].strip() if i + 1 < len(sections) else ""

            # Find the matching section
            for key, value in section_map.items():
                if value in section_header:
                    parts[key] = section_content
                    break

        # If parsing fails, attempt a fallback
        if not any(parts.values()):
            # Split into roughly equal parts
            lines = text.split("\n")
            section_length = len(lines) // 4

            parts = {
                "situation": "\n".join(lines[:section_length]).strip(),
                "task": "\n".join(lines[section_length : section_length * 2]).strip(),
                "action": "\n".join(
                    lines[section_length * 2 : section_length * 3]
                ).strip(),
                "result": "\n".join(lines[section_length * 3 :]).strip(),
            }

        # Ensure no section is empty
        for section in parts:
            if not parts[section].strip():
                parts[section] = f"No {section} information provided."

        return parts

    def _parse_evaluation_response(self, text: str) -> (str, Dict[str, int]):
        lines = text.splitlines()
        evaluation_lines = []
        scores = {}
        for line in lines:
            low = line.lower()
            if low.startswith("score"):
                try:
                    label, val = line.split(":", 1)
                    scores[label.strip()] = int(val.strip().split("/")[0])
                except Exception:
                    continue
            else:
                evaluation_lines.append(line)
        return ("\n".join(evaluation_lines).strip(), scores)
