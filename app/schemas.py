from pydantic import BaseModel, EmailStr
from typing import Optional, Generic, TypeVar, List
from datetime import datetime
from pydantic.generics import GenericModel


# ==========================
# 🔹 USER SCHEMAS
# ==========================
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


# ==========================
# 🔹 TASK SCHEMAS
# ==========================
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    github_link: Optional[str] = None
    hours_spent: Optional[float] = 0


class TaskCreate(TaskBase):
    owner_id: int


class TaskOut(TaskBase):
    id: int
    status: str
    owner_id: int
    assigned_by_id: int

    created_at: Optional[datetime]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    completed_at: Optional[datetime]

    time_taken: Optional[float]

    class Config:
        from_attributes = True


# ==========================
# 🔹 JOB CARD SCHEMAS
# ==========================
class JobCardBase(BaseModel):
    title: str
    description: Optional[str] = None
    github_link: Optional[str] = None


class JobCardCreate(JobCardBase):
    owner_id: int


class JobCardOut(JobCardBase):
    id: int
    status: str
    owner_id: int
    assigned_by_id: int

    created_at: Optional[datetime]
    opened_at: Optional[datetime]
    closed_at: Optional[datetime]

    duration: Optional[float]

    class Config:
        from_attributes = True


# ==========================
# 🔹 JOB UPDATE SCHEMA
# ==========================
class JobUpdateOut(BaseModel):
    id: int
    message: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==========================
# 🔹 NOTIFICATION SCHEMA
# ==========================
class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==========================
# 🔹 GENERIC RESPONSE SYSTEM
# ==========================
T = TypeVar("T")


class BaseResponse(GenericModel, Generic[T]):
    success: bool
    data: Optional[T]
    message: str


class PaginatedData(GenericModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int