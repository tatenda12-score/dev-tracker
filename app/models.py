from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import Boolean, DateTime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # ADMIN or USER
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import Text, Float, ForeignKey       
from sqlalchemy.orm import relationship


class Task(Base):
    __tablename__ = "tasks"
      
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    github_link = Column(String, nullable=True)
    hours_spent = Column(Float, nullable=False)

    completed_at = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User")
    
    

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))   # receiver
    sender_id = Column(Integer, ForeignKey("users.id")) # admin
    
    