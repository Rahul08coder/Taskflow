from pydantic import BaseModel, field_validator
from typing import Optional, Literal


class TaskCreate(BaseModel):
    title: str
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: Optional[str] = None
    project_id: int

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title cannot be blank")
        return value


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_date: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("title cannot be blank")
        return value


class TaskOut(BaseModel):
    id: int
    title: str
    priority: str
    due_date: Optional[str]
    project_id: int

    class Config:
        from_attributes = True