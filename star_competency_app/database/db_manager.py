# star_competency_app/database/db_manager.py
import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker
from sqlalchemy.orm.session import make_transient

from star_competency_app.config.settings import get_settings
from star_competency_app.database.models import (
    AuditLog,
    Base,
    CaseStudy,
    Competency,
    STARStory,
    User,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_url=None):
        settings = get_settings()
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_engine(self.db_url)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def create_tables(self):
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_user_by_azure_id(self, azure_id: str):
        """Get a user by their Azure ID."""
        with self.session_scope() as session:
            user = session.query(User).filter(User.azure_id == azure_id).first()
            if user:
                # Make a copy of important attributes before the session closes
                user._id = user.id
                user._is_admin = user.is_admin
                user._display_name = user.display_name
                user._email = user.email
                # Detach the user from session but keep state
                session.expunge(user)
            return user

    def get_user_by_id(self, user_id):
        """Get a user by their ID."""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                # Cache important attributes before session closes
                user._id = user.id
                user._is_admin = user.is_admin
                user._display_name = user.display_name
                user._email = user.email
                # Detach the user from session but keep state
                session.expunge(user)
            return user

    def create_user(self, azure_id, email, display_name):
        """Create a new user."""
        with self.session_scope() as session:
            user = User(azure_id=azure_id, email=email, display_name=display_name)
            session.add(user)
            session.commit()
            # Cache important properties before detaching
            user._id = user.id
            user._is_admin = user.is_admin
            user._display_name = user.display_name
            user._email = user.email
            # Detach from session
            session.expunge(user)
            return user

    def get_competencies(self):
        """Get all competencies."""
        with self.session_scope() as session:
            competencies = session.query(Competency).all()
            # Detach all objects from the session
            for comp in competencies:
                session.expunge(comp)
            return competencies

    def get_competency_by_id(self, competency_id):
        """Get a competency by its ID."""
        with self.session_scope() as session:
            competency = (
                session.query(Competency).filter(Competency.id == competency_id).first()
            )
            if competency:
                session.expunge(competency)
            return competency

    def create_competency(self, name, description, category=None, level=None):
        """Create a new competency."""
        with self.session_scope() as session:
            competency = Competency(
                name=name, description=description, category=category, level=level
            )
            session.add(competency)
            session.commit()
            session.expunge(competency)
            return competency

    def update_competency(
        self, competency_id, name=None, description=None, category=None, level=None
    ):
        """Update a competency."""
        with self.session_scope() as session:
            competency = (
                session.query(Competency).filter(Competency.id == competency_id).first()
            )
            if not competency:
                return None

            if name is not None:
                competency.name = name
            if description is not None:
                competency.description = description
            if category is not None:
                competency.category = category
            if level is not None:
                competency.level = level

            competency.updated_at = datetime.utcnow()
            session.commit()
            session.expunge(competency)
            return competency

    def delete_competency(self, competency_id):
        """Delete a competency."""
        with self.session_scope() as session:
            competency = (
                session.query(Competency).filter(Competency.id == competency_id).first()
            )
            if not competency:
                return False

            session.delete(competency)
            session.commit()
            return True

    def is_competency_in_use(self, competency_id):
        """Check if a competency is in use."""
        with self.session_scope() as session:
            story_count = (
                session.query(STARStory)
                .filter(STARStory.competency_id == competency_id)
                .count()
            )
            return story_count > 0

    def get_star_stories_by_user(self, user_id):
        """Get all STAR stories for a user."""
        with self.session_scope() as session:
            stories = (
                session.query(STARStory).filter(STARStory.user_id == user_id).all()
            )
            # Detach all stories from the session
            for story in stories:
                session.expunge(story)
            return stories

    def get_star_story_by_id(self, story_id):
        """Get a STAR story by its ID."""
        with self.session_scope() as session:
            story = session.query(STARStory).filter(STARStory.id == story_id).first()
            if story:
                session.expunge(story)
            return story

    def create_star_story(
        self,
        user_id,
        title,
        competency_id=None,
        situation=None,
        task=None,
        action=None,
        result=None,
    ):
        """Create a new STAR story."""
        with self.session_scope() as session:
            story = STARStory(
                user_id=user_id,
                competency_id=competency_id,
                title=title,
                situation=situation,
                task=task,
                action=action,
                result=result,
            )
            session.add(story)
            session.commit()
            session.expunge(story)
            return story

    def update_star_story(
        self,
        story_id,
        title=None,
        competency_id=None,
        situation=None,
        task=None,
        action=None,
        result=None,
        ai_feedback=None,
    ):
        """Update a STAR story."""
        with self.session_scope() as session:
            story = session.query(STARStory).filter(STARStory.id == story_id).first()
            if not story:
                return None

            if title is not None:
                story.title = title
            if competency_id is not None:
                story.competency_id = competency_id
            if situation is not None:
                story.situation = situation
            if task is not None:
                story.task = task
            if action is not None:
                story.action = action
            if result is not None:
                story.result = result
            if ai_feedback is not None:
                story.ai_feedback = ai_feedback

            story.updated_at = datetime.utcnow()
            session.commit()
            session.expunge(story)
            return story

    def delete_star_story(self, story_id):
        """Delete a STAR story."""
        with self.session_scope() as session:
            story = session.query(STARStory).filter(STARStory.id == story_id).first()
            if not story:
                return False

            session.delete(story)
            session.commit()
            return True

    def get_recent_star_stories_by_user(self, user_id, limit=3):
        """Get recent STAR stories for a user."""
        with self.session_scope() as session:
            stories = (
                session.query(STARStory)
                .filter(STARStory.user_id == user_id)
                .order_by(STARStory.updated_at.desc())
                .limit(limit)
                .all()
            )
            for story in stories:
                session.expunge(story)
            return stories

    def create_case_study(self, user_id, title, description=None, image_path=None):
        """Create a new case study."""
        with self.session_scope() as session:
            case_study = CaseStudy(
                user_id=user_id,
                title=title,
                description=description,
                image_path=image_path,
            )
            session.add(case_study)
            session.commit()
            session.expunge(case_study)
            return case_study

    def get_case_study_by_id(self, case_id):
        """Get a case study by its ID."""
        with self.session_scope() as session:
            case_study = (
                session.query(CaseStudy).filter(CaseStudy.id == case_id).first()
            )
            if case_study:
                session.expunge(case_study)
            return case_study

    def get_case_studies_by_user(self, user_id):
        """Get all case studies for a user."""
        with self.session_scope() as session:
            case_studies = (
                session.query(CaseStudy).filter(CaseStudy.user_id == user_id).all()
            )
            for study in case_studies:
                session.expunge(study)
            return case_studies

    def update_case_study(
        self,
        case_id,
        title=None,
        description=None,
        image_path=None,
        claude_analysis=None,
    ):
        """Update a case study."""
        with self.session_scope() as session:
            case_study = (
                session.query(CaseStudy).filter(CaseStudy.id == case_id).first()
            )
            if not case_study:
                return None

            if title is not None:
                case_study.title = title
            if description is not None:
                case_study.description = description
            if image_path is not None:
                case_study.image_path = image_path
            if claude_analysis is not None:
                case_study.claude_analysis = claude_analysis

            case_study.updated_at = datetime.utcnow()
            session.commit()
            session.expunge(case_study)
            return case_study

    def delete_case_study(self, case_id):
        """Delete a case study."""
        with self.session_scope() as session:
            case_study = (
                session.query(CaseStudy).filter(CaseStudy.id == case_id).first()
            )
            if not case_study:
                return False

            session.delete(case_study)
            session.commit()
            return True

    def log_audit(self, user_id, action, entity_type, entity_id=None, details=None):
        """Log an audit event."""
        with self.session_scope() as session:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
            session.add(audit)
            session.commit()

    def get_recent_audit_logs(self, user_id, action_type=None, limit=10):
        """Get recent audit logs for a user."""
        with self.session_scope() as session:
            query = session.query(AuditLog).filter(AuditLog.user_id == user_id)
            if action_type:
                query = query.filter(AuditLog.action == action_type)
            logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
            for log in logs:
                session.expunge(log)
            return logs

    def count_star_stories_by_user(self, user_id):
        """Count STAR stories for a user."""
        with self.session_scope() as session:
            return session.query(STARStory).filter(STARStory.user_id == user_id).count()

    def count_case_studies_by_user(self, user_id):
        """Count case studies for a user."""
        with self.session_scope() as session:
            return session.query(CaseStudy).filter(CaseStudy.user_id == user_id).count()

    def get_all_users(self):
        """Get all users."""
        with self.session_scope() as session:
            users = session.query(User).order_by(User.display_name).all()
            for user in users:
                user._id = user.id
                user._is_admin = user.is_admin
                session.expunge(user)
            return users

    def toggle_admin_role(self, user_id):
        """Toggle admin role for a user."""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            user.is_admin = not user.is_admin
            session.commit()
            return True

    def get_audit_logs_by_user(self, user_id):
        """Get all audit logs for a user."""
        with self.session_scope() as session:
            logs = (
                session.query(AuditLog)
                .filter(AuditLog.user_id == user_id)
                .order_by(AuditLog.created_at.desc())
                .all()
            )
            for log in logs:
                session.expunge(log)
            return logs

    def count_users(self):
        """Count total number of users."""
        with self.session_scope() as session:
            return session.query(User).count()

    def create_user(self, azure_id, email, display_name, is_admin=False):
        """Create a new user."""
        with self.session_scope() as session:
            user = User(
                azure_id=azure_id,
                email=email,
                display_name=display_name,
                is_admin=is_admin,
                is_active=True,
            )
            session.add(user)
            session.commit()
            # Cache important properties
            user._id = user.id
            user._is_admin = user.is_admin
            session.expunge(user)
            return user

    def update_user_if_changed(self, user_id, email=None, display_name=None):
        """Update user information if it has changed."""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            changes = False

            if email is not None and user.email != email:
                user.email = email
                changes = True

            if display_name is not None and user.display_name != display_name:
                user.display_name = display_name
                changes = True

            if changes:
                user.updated_at = datetime.utcnow()
                session.commit()

                # Log the update
                self.log_audit(
                    user_id=user_id,
                    action="user_updated",
                    entity_type="user",
                    entity_id=user_id,
                    details="User information updated from Azure AD",
                )

            # Cache important attributes
            user._id = user.id
            user._is_admin = user.is_admin
            user._display_name = user.display_name
            user._email = user.email
            session.expunge(user)
            return user
