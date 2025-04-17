from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(UserMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    azure_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    star_stories = relationship(
        "STARStory", back_populates="user", cascade="all, delete-orphan"
    )
    case_studies = relationship(
        "CaseStudy", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.display_name}>"

    def get_id(self):
        """Return the user's ID as a string."""
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_admin_safe(self):
        """
        Safely access is_admin attribute, handling detached instances.

        This method provides a way to access is_admin that works even
        when the instance is detached from a SQLAlchemy session.
        """
        try:
            # First, try to access the attribute normally
            return self.is_admin
        except Exception:
            # If that fails, return a default value
            return False

    @property
    def display_name_safe(self):
        """
        Safely access display_name attribute, handling detached instances.
        """
        try:
            return self.display_name
        except Exception:
            return ""

    @property
    def email_safe(self):
        """
        Safely access email attribute, handling detached instances.
        """
        try:
            return self.email
        except Exception:
            return ""


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    level = Column(Integer)
    expectations = Column(JSON)  # Store meets/exceeds expectations as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    star_stories = relationship("STARStory", back_populates="competency")

    def __repr__(self):
        return f"<Competency {self.name}>"


class STARStory(Base):
    __tablename__ = "star_stories"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"))
    title = Column(String, nullable=False)
    situation = Column(Text)
    task = Column(Text)
    action = Column(Text)
    result = Column(Text)
    ai_feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="star_stories")
    competency = relationship("Competency", back_populates="star_stories")

    def __repr__(self):
        return f"<STARStory {self.title}>"


class CaseStudy(Base):
    __tablename__ = "case_studies"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    image_path = Column(String)
    claude_analysis = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="case_studies")

    def __repr__(self):
        return f"<CaseStudy {self.title}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}>"
