import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload, scoped_session, sessionmaker

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

        # Configure session with additional options to help with detached instances
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,  # Prevent objects being expired on commit
            autoflush=True,  # Auto-flush changes to DB
            autocommit=False,  # Explicit transaction management
        )

        # Thread-local sessions
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
        """
        Provide a transactional scope around operations.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            # This explicitly closes the session
            session.close()
            # This removes the session from the registry
            self.Session.remove()

    def _load_objects_with_relationships(
        self, model_class, filters=None, relationships=None, order_by=None, limit=None
    ):
        """
        Load objects with specified relationships.

        Args:
            model_class: The SQLAlchemy model class
            filters: List of filter conditions to apply
            relationships: List of relationship attributes to eager load
            order_by: Optional order by clause
            limit: Optional limit on results
        """
        with self.session_scope() as session:
            query = session.query(model_class)

            # Apply filters
            if filters:
                for filter_condition in filters:
                    query = query.filter(filter_condition)

            # Apply eager loading
            if relationships:
                for rel in relationships:
                    query = query.options(joinedload(rel))

            # Apply ordering
            if order_by:
                query = query.order_by(order_by)

            # Apply limit
            if limit:
                query = query.limit(limit)

            return query.all()

    def refresh_object(self, obj, relationships=None):
        """
        Refresh a potentially detached object with a new session.

        Args:
            obj: The SQLAlchemy object that might be detached
            relationships: List of relationship attributes to eager load

        Returns:
            A refreshed copy of the object with all attributes loaded
        """
        if obj is None:
            return None

        with self.session_scope() as session:
            # Get the class of the object
            obj_class = obj.__class__

            # Create a query with the primary key
            query = session.query(obj_class).filter_by(id=obj.id)

            # Add eager loading if requested
            if relationships:
                for rel in relationships:
                    query = query.options(joinedload(rel))

            # Return a fresh copy of the object
            return query.first()

    def get_user_by_azure_id(self, azure_id: str):
        """Get a user by their Azure ID."""
        with self.session_scope() as session:
            return session.query(User).filter(User.azure_id == azure_id).first()

    def get_user_by_id(self, user_id: int):
        """Get a user by their ID."""
        with self.session_scope() as session:
            return session.query(User).filter(User.id == user_id).first()

    def create_user(self, azure_id: str, email: str, display_name: str, is_admin=False):
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
            session.flush()  # Ensure ID is generated
            return user

    def get_competencies(self):
        """Get all competencies."""
        return self._load_objects_with_relationships(model_class=Competency)

    def get_competency_by_id(self, competency_id: int):
        """Get a competency by its ID."""
        with self.session_scope() as session:
            return (
                session.query(Competency).filter(Competency.id == competency_id).first()
            )

    def create_competency(self, name: str, description: str, category=None, level=None):
        """Create a new competency."""
        with self.session_scope() as session:
            comp = Competency(
                name=name, description=description, category=category, level=level
            )
            session.add(comp)
            session.flush()  # Ensure ID is generated
            return comp

    def update_competency(
        self, competency_id: int, name=None, description=None, category=None, level=None
    ):
        """Update a competency."""
        with self.session_scope() as session:
            comp = (
                session.query(Competency).filter(Competency.id == competency_id).first()
            )
            if not comp:
                return None
            if name is not None:
                comp.name = name
            if description is not None:
                comp.description = description
            if category is not None:
                comp.category = category
            if level is not None:
                comp.level = level
            comp.updated_at = datetime.utcnow()
            return comp

    def delete_competency(self, competency_id: int) -> bool:
        """Delete a competency."""
        with self.session_scope() as session:
            comp = (
                session.query(Competency).filter(Competency.id == competency_id).first()
            )
            if not comp:
                return False
            session.delete(comp)
            return True

    def is_competency_in_use(self, competency_id: int) -> bool:
        """Check if a competency is in use."""
        with self.session_scope() as session:
            return (
                session.query(STARStory)
                .filter(STARStory.competency_id == competency_id)
                .count()
                > 0
            )

    def get_star_stories_by_user(self, user_id: int):
        """Get all STAR stories for a user with eager loading."""
        return self._load_objects_with_relationships(
            model_class=STARStory,
            filters=[STARStory.user_id == user_id],
            relationships=[STARStory.competency],
        )

    def get_star_story_by_id(self, story_id: int):
        """Get a STAR story by its ID with eager loading."""
        with self.session_scope() as session:
            return (
                session.query(STARStory)
                .options(joinedload(STARStory.competency))
                .filter(STARStory.id == story_id)
                .first()
            )

    def create_star_story(
        self,
        user_id: int,
        title: str,
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
            session.flush()  # Ensure ID is generated
            return story

    def update_star_story(
        self,
        story_id: int,
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
            for field, value in [
                ("title", title),
                ("competency_id", competency_id),
                ("situation", situation),
                ("task", task),
                ("action", action),
                ("result", result),
                ("ai_feedback", ai_feedback),
            ]:
                if value is not None:
                    setattr(story, field, value)
            story.updated_at = datetime.utcnow()
            return story

    def delete_star_story(self, story_id: int) -> bool:
        """Delete a STAR story."""
        with self.session_scope() as session:
            story = session.query(STARStory).filter(STARStory.id == story_id).first()
            if not story:
                return False
            session.delete(story)
            return True

    def get_recent_star_stories_by_user(self, user_id: int, limit=3):
        """Get recent STAR stories for a user."""
        return self._load_objects_with_relationships(
            model_class=STARStory,
            filters=[STARStory.user_id == user_id],
            relationships=[STARStory.competency],
            order_by=STARStory.updated_at.desc(),
            limit=limit,
        )

    def create_case_study(
        self, user_id: int, title: str, description=None, image_path=None
    ):
        """Create a new case study."""
        with self.session_scope() as session:
            cs = CaseStudy(
                user_id=user_id,
                title=title,
                description=description,
                image_path=image_path,
            )
            session.add(cs)
            session.flush()  # Ensure ID is generated
            return cs

    def get_case_study_by_id(self, case_id: int):
        """Get a case study by its ID."""
        with self.session_scope() as session:
            return session.query(CaseStudy).filter(CaseStudy.id == case_id).first()

    def get_case_studies_by_user(self, user_id: int):
        """Get all case studies for a user."""
        return self._load_objects_with_relationships(
            model_class=CaseStudy, filters=[CaseStudy.user_id == user_id]
        )

    def update_case_study(
        self,
        case_id: int,
        title=None,
        description=None,
        image_path=None,
        claude_analysis=None,
    ):
        """Update a case study."""
        with self.session_scope() as session:
            cs = session.query(CaseStudy).filter(CaseStudy.id == case_id).first()
            if not cs:
                return None
            for field, value in [
                ("title", title),
                ("description", description),
                ("image_path", image_path),
                ("claude_analysis", claude_analysis),
            ]:
                if value is not None:
                    setattr(cs, field, value)
            cs.updated_at = datetime.utcnow()
            return cs

    def delete_case_study(self, case_id: int) -> bool:
        """Delete a case study."""
        with self.session_scope() as session:
            cs = session.query(CaseStudy).filter(CaseStudy.id == case_id).first()
            if not cs:
                return False
            session.delete(cs)
            return True

    def log_audit(
        self, user_id: int, action: str, entity_type: str, entity_id=None, details=None
    ):
        """Log an audit event."""
        with self.session_scope() as session:
            log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
            session.add(log)
            return log

    def get_recent_audit_logs(self, user_id: int, action_type=None, limit=10):
        """Get recent audit logs for a user."""
        filters = [AuditLog.user_id == user_id]
        if action_type:
            filters.append(AuditLog.action == action_type)

        return self._load_objects_with_relationships(
            model_class=AuditLog,
            filters=filters,
            order_by=AuditLog.created_at.desc(),
            limit=limit,
        )

    def count_star_stories_by_user(self, user_id: int) -> int:
        """Count STAR stories for a user."""
        with self.session_scope() as session:
            return session.query(STARStory).filter(STARStory.user_id == user_id).count()

    def count_case_studies_by_user(self, user_id: int) -> int:
        """Count case studies for a user."""
        with self.session_scope() as session:
            return session.query(CaseStudy).filter(CaseStudy.user_id == user_id).count()

    def get_all_users(self):
        """Get all users."""
        return self._load_objects_with_relationships(
            model_class=User, order_by=User.display_name
        )

    def toggle_admin_role(self, user_id: int):
        """Toggle admin role for a user."""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.is_admin = not user.is_admin
            return user

    def get_audit_logs_by_user(self, user_id: int):
        """Get all audit logs for a user."""
        return self._load_objects_with_relationships(
            model_class=AuditLog,
            filters=[AuditLog.user_id == user_id],
            order_by=AuditLog.created_at.desc(),
        )

    def count_users(self) -> int:
        """Count total number of users."""
        with self.session_scope() as session:
            return session.query(User).count()

    def update_user_if_changed(self, user_id: int, email=None, display_name=None):
        """Update user information if it has changed."""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            changed = False
            if email is not None and user.email != email:
                user.email = email
                changed = True
            if display_name is not None and user.display_name != display_name:
                user.display_name = display_name
                changed = True
            if changed:
                user.updated_at = datetime.utcnow()
                # log inside same session
                session.add(
                    AuditLog(
                        user_id=user_id,
                        action="user_updated",
                        entity_type="user",
                        entity_id=user_id,
                        details="User information synced from Azure",
                    )
                )
            return user
