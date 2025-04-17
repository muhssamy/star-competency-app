# star_competency_app/utils/text_utils.py
import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_star_components(text: str) -> Dict[str, str]:
    """
    Extract STAR components from text.

    Args:
        text: Text containing STAR components

    Returns:
        Dict with situation, task, action, result
    """
    components = {"situation": "", "task": "", "action": "", "result": ""}

    # Define patterns for each component
    patterns = {
        "situation": [
            r"(?:^|\n)situation[:\s]+(.*?)(?=\n(?:task|action|result)[:\s]|$)",
            r"(?:^|\n)s[:\s]+(.*?)(?=\n(?:t|a|r)[:\s]|$)",
        ],
        "task": [
            r"(?:^|\n)task[:\s]+(.*?)(?=\n(?:situation|action|result)[:\s]|$)",
            r"(?:^|\n)t[:\s]+(.*?)(?=\n(?:s|a|r)[:\s]|$)",
        ],
        "action": [
            r"(?:^|\n)action[:\s]+(.*?)(?=\n(?:situation|task|result)[:\s]|$)",
            r"(?:^|\n)a[:\s]+(.*?)(?=\n(?:s|t|r)[:\s]|$)",
        ],
        "result": [
            r"(?:^|\n)result[:\s]+(.*?)(?=\n(?:situation|task|action)[:\s]|$)",
            r"(?:^|\n)r[:\s]+(.*?)(?=\n(?:s|t|a)[:\s]|$)",
        ],
    }

    # Try to extract each component
    for component, component_patterns in patterns.items():
        for pattern in component_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                components[component] = match.group(1).strip()
                break

    return components


def normalize_competency_name(name: str) -> str:
    """
    Normalize a competency name for comparison.

    Args:
        name: Competency name

    Returns:
        Normalized competency name
    """
    # Remove punctuation and extra spaces
    normalized = re.sub(r"[^\w\s]", "", name).lower()
    # Replace multiple spaces with a single space
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def find_matching_competencies(text: str, competencies: List[Dict]) -> List[Dict]:
    """
    Find competencies mentioned in text.

    Args:
        text: Text to search for competencies
        competencies: List of competency dictionaries

    Returns:
        List of matching competencies
    """
    if not text or not competencies:
        return []

    text_lower = text.lower()
    matches = []

    for comp in competencies:
        name = comp.get("name", "")
        normalized_name = normalize_competency_name(name)

        # Look for exact matches or variations
        if normalized_name in normalize_competency_name(text_lower):
            matches.append(comp)
            continue

        # Check for partial matches on words
        words = normalized_name.split()
        if len(words) > 1:
            match_count = 0
            for word in words:
                if (
                    len(word) > 3 and word in text_lower
                ):  # Only consider significant words
                    match_count += 1

            # If more than half the words match, consider it a match
            if match_count >= len(words) / 2:
                matches.append(comp)

    return matches


def summarize_text(text: str, max_length: int = 200) -> str:
    """
    Create a concise summary of text.

    Args:
        text: Text to summarize
        max_length: Maximum length of summary

    Returns:
        Summarized text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)

    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) <= max_length:
            summary += sentence + " "
        else:
            break

    return summary.strip()
