from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.sql import func
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
    role = Column(String, nullable=False)  # ADMIN or USER
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==========================
# TASK MODEL (UPDATED)
# ==========================
class Task(Base):
    __tablename__ = "tasks"
      
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"))
    assigned_by_id = Column(Integer, ForeignKey("users.id"))

    status = Column(String, default="Pending")  # ✅ IMPORTANT
    
    created_at = Column(DateTime, default=datetime.now)

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    time_taken = Column(Float, nullable=True)  # seconds

    owner = relationship("User", foreign_keys=[owner_id])


# ==========================
# NOTIFICATION MODEL
# ==========================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))   # receiver
    sender_id = Column(Integer, ForeignKey("users.id")) # admin