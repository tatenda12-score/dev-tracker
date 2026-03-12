from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    github_link: Optional[str] = None
    hours_spent: int
    
    

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: int
    completed_at: datetime
    owner_id: int

    class Config:
     from_attributes = True
     
from typing import Generic, TypeVar, List
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


# Standard API Response Wrapper
class BaseResponse(GenericModel, Generic[T]):
    success: bool
    data: T
    message: str


# Pagination Data Wrapper
class PaginationMeta(BaseModel):
    total: int
    skip: int
    limit: int


class PaginatedData(GenericModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int
    
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    hours_spent: int
    github_link: Optional[str]
    completed_at: datetime
    owner_id: int

    class Config:
        from_attributes = True