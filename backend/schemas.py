# =====================================================
# Pydantic Schemas for TaskFlow API
# =====================================================

# Import Pydantic components for data validation and serialization
from pydantic import BaseModel, field_validator, Field
from typing import Optional, Literal

# =====================================================
# User Schemas
# =====================================================

class UserCreate(BaseModel):
    """Schema for creating a new user (legacy)"""
    email: str
    name: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        """Validate that name is not empty or whitespace only"""
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value


class UserOut(BaseModel):
    """Schema for user response data"""
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models


# ===================================================================
# AUTH SCHEMAS (new) — used by /auth/register and /auth/login
# ===================================================================

class UserRegister(BaseModel):
    """Request body for POST /auth/register - creates new user account"""
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        """Validate name is not empty"""
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value

    @field_validator("password")
    @classmethod
    def password_min_length(cls, value: str) -> str:
        """Validate password minimum length (hashing handled separately)"""
        if len(value) < 6:
            raise ValueError("password must be at least 6 characters")
        return value


class UserLoginRequest(BaseModel):
    """Request body for POST /auth/login - user authentication"""
    email: str
    password: str


class AuthResponse(BaseModel):
    """Response body for POST /auth/login - returns session token"""
    token: str
    user_id: int
    name: str
    email: str
    is_admin: bool


class NotificationOut(BaseModel):
    """Schema for notification response data"""
    id: int
    message: str
    type: str
    is_read: bool

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Request body for chat endpoint"""
    message: str


class ChatResponse(BaseModel):
    """Response body for chat endpoint"""
    reply: str


class ProjectCreate(BaseModel):
    """Schema for creating a new project - owner is determined from auth token"""
    name: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        """Validate project name is not empty"""
        if not value.strip():
            raise ValueError("name cannot be blank")
        return value


class ProjectOut(BaseModel):
    """Schema for project response data"""
    id: int
    name: str
    owner_id: int

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    """Schema for creating a new task with validation"""
    title: str
    priority: Literal["low", "medium", "high"] = Field(default="medium")
    status: Literal["pending", "in_progress", "completed"] = "pending"
    due_date: Optional[str] = None
    project_id: int

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        """Validate task title is not empty"""
        if not value.strip():
            raise ValueError("title cannot be blank")
        return value


class QuickAddRequest(BaseModel):
    """Schema for quick task creation from natural language description"""
    description: str
    project_id: int


class TaskUpdate(BaseModel):
    """Schema for updating existing task - all fields optional"""
    title: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high"]] = Field(default=None)
    status: Optional[Literal["pending", "in_progress", "completed"]] = None
    due_date: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: Optional[str]) -> Optional[str]:
        """Validate title if provided (not empty)"""
        if value is not None and not value.strip():
            raise ValueError("title cannot be blank")
        return value


class TaskOut(BaseModel):
    """Schema for task response data - includes all task fields"""
    id: int
    title: str
    priority: str
    status: str
    due_date: Optional[str]
    project_id: int

    class Config:
        from_attributes = True