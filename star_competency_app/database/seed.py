# star_competency_app/database/seed.py
import json
import logging

from star_competency_app.config.competencies import COMPETENCIES
from star_competency_app.database.db_manager import DatabaseManager
from star_competency_app.database.models import Competency

logger = logging.getLogger(__name__)


def seed_competencies(db_manager=None):
    """
    Seed the database with predefined competencies.
    Only adds competencies that don't already exist (based on name).
    """
    if db_manager is None:
        db_manager = DatabaseManager()

    try:
        with db_manager.session_scope() as session:
            # Get existing competency names
            existing_competencies = session.query(Competency.name).all()
            existing_names = [comp[0] for comp in existing_competencies]

            # Add competencies that don't already exist
            added_count = 0
            for comp_data in COMPETENCIES:
                if comp_data["name"] not in existing_names:
                    expectations = {}
                    if "expectations" in comp_data:
                        expectations = comp_data["expectations"]

                    competency = Competency(
                        name=comp_data["name"],
                        description=comp_data["description"],
                        category=comp_data.get("category"),
                        level=comp_data.get("level"),
                        expectations=expectations,
                    )
                    session.add(competency)
                    added_count += 1

            session.commit()

            if added_count > 0:
                logger.info(f"Added {added_count} new competencies to the database")
            else:
                logger.info("No new competencies added (all already exist)")

            return added_count
    except Exception as e:
        logger.error(f"Error seeding competencies: {e}")
        return 0
