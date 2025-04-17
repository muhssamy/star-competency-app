# star_competency_app/main.py
import logging
import os

from star_competency_app.database.db_manager import DatabaseManager
from star_competency_app.database.seed import seed_competencies
from star_competency_app.interfaces.web.app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    try:
        logger.info("Initializing STAR Competency App")

        # Initialize database
        db_manager = DatabaseManager()
        logger.info("Ensuring database tables exist")
        db_manager.create_tables()

        # Seed competencies
        logger.info("Seeding competencies")
        seed_competencies(db_manager)

        # Ensure required directories exist
        from star_competency_app.config.settings import get_settings

        settings = get_settings()
        os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
        logger.info(f"Ensured upload directory exists: {settings.UPLOAD_FOLDER}")

        # Start the Flask application
        logger.info("Starting web application")
        app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)

    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise


if __name__ == "__main__":
    main()
