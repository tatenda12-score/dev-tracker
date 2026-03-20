from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


# ==========================
# USER MODEL
# ==========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="USER")

    created_at = Column(DateTime, default=datetime.utcnow)

    # 🔗 Relationships
    tasks = relationship("Task", foreign_keys="Task.owner_id", back_populates="owner")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_by_id")

    job_cards = relationship("JobCard", foreign_keys="JobCard.owner_id", back_populates="owner")
    assigned_jobs = relationship("JobCard", foreign_keys="JobCard.assigned_by_id")

    notifications = relationship("Notification", foreign_keys="Notification.user_id", back_populates="user")


# ==========================
# TASK MODEL
# ==========================
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    github_link = Column(String, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(String, default="Pending", index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    time_taken = Column(Float, nullable=True)  # seconds
    hours_spent = Column(Float, default=0)     # for analytics

    completed_at = Column(DateTime, nullable=True)

    # 🔗 Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="tasks")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


# ==========================
# JOB CARD MODEL
# ==========================
class JobCard(Base):
    __tablename__ = "job_cards"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    github_link = Column(String, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(String, default="Pending", index=True)  # Pending, Open, Closed

    created_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    duration = Column(Float, nullable=True)  # seconds

    # 🔗 Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="job_cards")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])

    updates = relationship("JobUpdate", back_populates="job", cascade="all, delete-orphan")


# ==========================
# JOB UPDATE MODEL
# ==========================
class JobUpdate(Base):
    __tablename__ = "job_updates"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer, ForeignKey("job_cards.id"), nullable=False)
    message = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 🔗 Relationship
    job = relationship("JobCard", back_populates="updates")


# ==========================
# NOTIFICATION MODEL
# ==========================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 🔗 Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    sender = relationship("User", foreign_keys=[sender_id])