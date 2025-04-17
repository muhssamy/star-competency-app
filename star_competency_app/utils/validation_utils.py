# star_competency_app/utils/validation_utils.py
import imghdr
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import bleach
from marshmallow import Schema, ValidationError, fields, validates, validates_schema

# Maximum allowed file size (16MB)
MAX_FILE_SIZE = 16 * 1024 * 1024

# Allowed image file types
ALLOWED_IMAGE_TYPES = {"jpeg", "jpg", "png", "gif"}


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        html_content: The HTML content to sanitize

    Returns:
        Sanitized HTML content
    """
    if not html_content:
        return ""

    allowed_tags = [
        "p",
        "br",
        "strong",
        "em",
        "u",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "span",
        "div",
        "b",
        "i",
    ]
    allowed_attributes = {"*": ["class", "style"]}
    return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attributes)


def sanitize_input(
    data: Dict[str, Any], fields_to_sanitize: List[str]
) -> Dict[str, Any]:
    """
    Sanitize multiple fields in input data.

    Args:
        data: Dictionary of input data
        fields_to_sanitize: List of field names to sanitize

    Returns:
        Dictionary with sanitized data
    """
    sanitized_data = data.copy()
    for field in fields_to_sanitize:
        if field in sanitized_data and sanitized_data[field]:
            sanitized_data[field] = sanitize_html(sanitized_data[field])
    return sanitized_data


def validate_image_file(file) -> Tuple[bool, Optional[str]]:
    """
    Validate an uploaded image file.

    Args:
        file: The uploaded file object

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer

    if file_size > MAX_FILE_SIZE:
        return (
            False,
            f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024 * 1024)}MB)",
        )

    # Check file type
    file_type = imghdr.what(file)
    if not file_type or file_type.lower() not in ALLOWED_IMAGE_TYPES:
        return (
            False,
            f"File type not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    return True, None


# Schema Definitions
class CompetencySchema(Schema):
    """Schema for validating competency data."""

    name = fields.String(required=True, validate=lambda s: 2 <= len(s) <= 255)
    description = fields.String(required=True)
    category = fields.String(allow_none=True)
    level = fields.Integer(
        allow_none=True, validate=lambda n: 1 <= n <= 5 if n is not None else True
    )

    @validates("name")
    def validate_name(self, value):
        """Validate competency name."""
        if not value.strip():
            raise ValidationError("Competency name cannot be empty or whitespace.")


class STARStorySchema(Schema):
    """Schema for validating STAR story input."""

    title = fields.String(required=True, validate=lambda s: 2 <= len(s) <= 255)
    situation = fields.String(required=True)
    task = fields.String(required=True)
    action = fields.String(required=True)
    result = fields.String(required=True)
    competency_id = fields.Integer(allow_none=True)

    @validates("title")
    def validate_title(self, value):
        """Validate story title."""
        if not value.strip():
            raise ValidationError("Title cannot be empty or whitespace.")

    @validates_schema
    def validate_star_components(self, data, **kwargs):
        """Validate that all STAR components have meaningful content."""
        for component in ["situation", "task", "action", "result"]:
            if component in data and (
                not data[component] or len(data[component].strip()) < 10
            ):
                raise ValidationError(
                    f"The {component} component must have meaningful content (at least 10 characters).",
                    component,
                )


class CaseStudySchema(Schema):
    """Schema for validating case study input."""

    title = fields.String(required=True, validate=lambda s: 2 <= len(s) <= 255)
    description = fields.String(allow_none=True)

    @validates("title")
    def validate_title(self, value):
        """Validate case study title."""
        if not value.strip():
            raise ValidationError("Title cannot be empty or whitespace.")


# Validation Functions
def validate_star_story(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate STAR story data.

    Args:
        data: Dictionary containing STAR story data

    Returns:
        Tuple of (is_valid, validated_data_or_errors)
    """
    try:
        schema = STARStorySchema()
        validated_data = schema.load(data)

        # Sanitize HTML content
        sanitized_data = sanitize_input(
            validated_data, ["situation", "task", "action", "result"]
        )

        return True, sanitized_data
    except ValidationError as err:
        return False, err.messages


def validate_case_study(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate case study data.

    Args:
        data: Dictionary containing case study data

    Returns:
        Tuple of (is_valid, validated_data_or_errors)
    """
    try:
        schema = CaseStudySchema()
        validated_data = schema.load(data)

        # Sanitize HTML content
        sanitized_data = sanitize_input(validated_data, ["description"])

        return True, sanitized_data
    except ValidationError as err:
        return False, err.messages


def validate_competency(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate competency data.

    Args:
        data: Dictionary containing competency data

    Returns:
        Tuple of (is_valid, validated_data_or_errors)
    """
    try:
        schema = CompetencySchema()
        validated_data = schema.load(data)

        # Sanitize HTML content
        sanitized_data = sanitize_input(validated_data, ["description"])

        return True, sanitized_data
    except ValidationError as err:
        return False, err.messages
