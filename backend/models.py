# =====================================================
# SQLAlchemy Database Models for TaskFlow
# =====================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    """User model - stores account and authentication data"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    # --- AUTH FIELDS ---
    # Stores bcrypt hash of password, never raw password
    password_hash = Column(String, nullable=True)

    # Session token for authentication - unique for quick user lookup
    session_token = Column(String, unique=True, nullable=True, index=True)

    # Admin flag - allows access to admin-only endpoints
    is_admin = Column(Boolean, nullable=False, default=False)

    # Account creation timestamp for tracking new registrations
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship: User owns multiple projects
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    """Project model - contains tasks and belongs to a user"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")


class Task(Base):
    """Task model - individual tasks within projects"""
    __tablename__ = "tasks"
    
    # Constraints to ensure valid priority and status values
    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="check_priority"),
        CheckConstraint("status IN ('pending', 'in_progress', 'completed')", name="check_status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    priority = Column(String, nullable=False, default="medium")
    status = Column(String, nullable=False, default="pending")
    due_date = Column(String, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relationship: Task belongs to a project
    project = relationship("Project", back_populates="tasks")


class Notification(Base):
    """Notification model - system notifications for users"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Recipient user ID - for task/project events or admin alerts
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    message = Column(String, nullable=False)
    
    # Notification type: "task", "project", "quick_add", "registration"
    type = Column(String, nullable=False)

    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship: Notification belongs to a user
    user = relationship("User")