# star_competency_app/utils/image_utils.py
import logging
import os
import uuid
from typing import Optional

import pytesseract
from PIL import Image

from star_competency_app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def is_allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in settings.ALLOWED_EXTENSIONS
    )


def save_uploaded_image(file, user_id: int) -> Optional[str]:
    """
    Save an uploaded image file and return its path.

    Args:
        file: The uploaded file object
        user_id: User ID for organizing files

    Returns:
        Path to the saved file or None if failed
    """
    try:
        if not file or not is_allowed_file(file.filename):
            logger.warning(
                f"Invalid file upload attempt: {file.filename if file else 'None'}"
            )
            return None

        # Create user directory if it doesn't exist
        user_dir = os.path.join(settings.UPLOAD_FOLDER, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        # Generate unique filename
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        file_path = os.path.join(user_dir, filename)

        # Save the file
        file.save(file_path)
        logger.info(f"Saved image: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return None


def extract_text_from_image(image_path: str) -> Optional[str]:
    """
    Extract text from an image using OCR.

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text or None if failed
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return None

        # Open image with PIL
        image = Image.open(image_path)

        # Preprocess image for better OCR results
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")

        # Perform OCR
        text = pytesseract.image_to_string(image)

        if not text.strip():
            logger.warning(f"No text extracted from image: {image_path}")

        return text

    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return None


def get_image_dimensions(image_path: str) -> Optional[tuple]:
    """
    Get the dimensions of an image.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (width, height) or None if failed
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return None

        # Open image with PIL
        image = Image.open(image_path)
        return image.size

    except Exception as e:
        logger.error(f"Error getting image dimensions: {e}")
        return None
