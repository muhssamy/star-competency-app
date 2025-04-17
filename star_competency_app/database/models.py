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

    # Flask-Login integration with safe detached instance handling
    def get_id(self):
        """Return user ID as string, safely handling detached instances."""
        if hasattr(self, "_id"):
            return str(self._id)
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_admin_safe(self):
        """Safe accessor for is_admin that works with detached objects."""
        if hasattr(self, "_is_admin"):
            return self._is_admin
        return getattr(self, "is_admin", False)

    @property
    def display_name_safe(self):
        """Safe accessor for display_name that works with detached objects."""
        if hasattr(self, "_display_name"):
            return self._display_name
        return getattr(self, "display_name", "")

    @property
    def email_safe(self):
        """Safe accessor for email that works with detached objects."""
        if hasattr(self, "_email"):
            return self._email
        return getattr(self, "email", "")


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
