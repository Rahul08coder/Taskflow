from pydantic import BaseModel, field_validator, Field
from typing import Optional, Literal




class UserCreate(BaseModel):
    email: str
    name: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value


class UserOut(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    owner_id: int

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value


class ProjectOut(BaseModel):
    id: int
    name: str
    owner_id: int

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):   #Schema for Creating a New Task
    title: str
    priority: Literal["low", "medium", "high"] = Field(default="medium")
    status: Literal["pending", "in_progress", "completed"] = "pending"
    due_date: Optional[str] = None
    project_id: int

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title cannot be blank")
        return value


class QuickAddRequest(BaseModel):
    description: str
    project_id: int


class TaskUpdate(BaseModel):       #Schema for Updating existing data
    title: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high"]] = Field(default=None)
    status: Optional[Literal["pending", "in_progress", "completed"]] = None
    due_date: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("title cannot be blank")
        return value


class TaskOut(BaseModel):    #Response schema
    id: int
    title: str
    priority: str
    status: str
    due_date: Optional[str]
    project_id: int

    class Config:
        from_attributes = True