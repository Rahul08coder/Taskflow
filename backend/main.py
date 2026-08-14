# =====================================================
# FastAPI Main Application - TaskFlow API Server
# =====================================================

from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Task

from quick_add_parser import parse_description
from schemas import (
    TaskCreate, TaskUpdate, TaskOut, UserCreate, UserOut, ProjectCreate, ProjectOut,
    QuickAddRequest,
    UserRegister, UserLoginRequest, AuthResponse,
    NotificationOut,
    ChatRequest, ChatResponse,
)

import os
import requests

from auth_utils import hash_password, verify_password, generate_session_token

from algorithms import insertion_sort, binary_search, linear_search
from typing import Optional
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}

import time
import logging

from fastapi.middleware.cors import CORSMiddleware

from database import get_db
import models

# Initialize FastAPI application
app = FastAPI(title="Taskflow API")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("taskflow")

# Configure CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "https://taskflow-frontend-g67g.onrender.com",
],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Middleware to log all incoming requests with timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000

    logger.info(
        f"{request.method} {request.url.path} - {process_time_ms:.2f}ms"
    )
    return response

# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Taskflow API is running"}

# ===================================================================
# AUTH DEPENDENCIES
# ===================================================================

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> models.User:
    """Extract and validate user from session token in Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    user = db.query(models.User).filter(models.User.session_token == token).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Ensure current user has admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def create_notification(db: Session, user_id: int, message: str, ntype: str) -> None:
    """Create and save a notification for a user"""
    notif = models.Notification(user_id=user_id, message=message, type=ntype)
    db.add(notif)
    db.commit()

# ===================================================================
# AUTH ENDPOINTS
# ===================================================================

@app.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account"""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Notify all admins about new registration
    admins = db.query(models.User).filter(models.User.is_admin == True).all()
    for admin in admins:
        create_notification(
            db, admin.id,
            f"New user registered: {new_user.name} ({new_user.email})",
            "registration",
        )

    return new_user

@app.post("/auth/login", response_model=AuthResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return session token"""
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = generate_session_token()
    user.session_token = token
    db.commit()

    return AuthResponse(
        token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        is_admin=user.is_admin,
    )

@app.post("/auth/logout")
def logout(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout user by clearing session token"""
    current_user.session_token = None
    db.commit()
    return {"message": "Logged out successfully"}

# NOTE: old unauthenticated endpoints (kept for backward compatibility)

@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Legacy user creation endpoint"""
    new_user = models.User(email=user.email, name=user.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users", response_model=list[UserOut])
def get_users(current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    """Admin-only endpoint to list all users"""
    users = db.query(models.User).all()
    return users

# ===================================================================
# ADMIN ENDPOINTS
# ===================================================================

@app.get("/admin/users")
def get_all_users_with_counts(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: list all users with their project and task counts"""
    users = db.query(models.User).all()

    result = []
    for u in users:
        project_count = (
            db.query(func.count(models.Project.id))
            .filter(models.Project.owner_id == u.id)
            .scalar()
        )
        task_count = (
            db.query(func.count(models.Task.id))
            .join(models.Project, models.Task.project_id == models.Project.id)
            .filter(models.Project.owner_id == u.id)
            .scalar()
        )
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "is_admin": u.is_admin,
            "project_count": project_count,
            "task_count": task_count,
        })

    return result

@app.get("/admin/users/{user_id}/detail")
def get_user_detail_admin(
    user_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: get detailed information about a specific user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    projects = db.query(models.Project).filter(models.Project.owner_id == user_id).all()
    tasks = (
        db.query(models.Task)
        .join(models.Project, models.Task.project_id == models.Project.id)
        .filter(models.Project.owner_id == user_id)
        .all()
    )

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email, "is_admin": user.is_admin},
        "projects": [{"id": p.id, "name": p.name} for p in projects],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date,
                "project_id": t.project_id,
            }
            for t in tasks
        ],
    }

# ===================================================================
# PROJECTS ENDPOINTS
# ===================================================================

@app.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project for the authenticated user"""
    new_project = models.Project(name=project.name, owner_id=current_user.id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    create_notification(db, current_user.id, f"New project created: {new_project.name}", "project")

    return new_project

@app.get("/projects", response_model=list[ProjectOut])
def get_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all projects owned by the authenticated user"""
    projects = db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()
    return projects

# ===================================================================
# TASKS ENDPOINTS
# ===================================================================

@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task in a project owned by the user"""
    project = (
        db.query(models.Project)
        .filter(models.Project.id == task.project_id, models.Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_task = models.Task(
        title=task.title,
        priority=task.priority,
        status=task.status,
        due_date=task.due_date,
        project_id=task.project_id,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    create_notification(db, current_user.id, f"New task created: {new_task.title}", "task")

    return new_task

@app.post("/tasks/quick-add", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def quick_add_task(
    payload: QuickAddRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a task from natural language description"""
    project = (
        db.query(models.Project)
        .filter(models.Project.id == payload.project_id, models.Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=422,
            detail="project_id does not reference an existing project you own",
        )

    parsed = parse_description(payload.description)

    new_task = models.Task(
        title=parsed["title"],
        priority=parsed["priority"],
        status="pending",
        due_date=parsed["due_date_hint"],
        project_id=payload.project_id,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    create_notification(db, current_user.id, f"Quick-added task: {new_task.title}", "quick_add")

    return new_task

@app.get("/tasks", response_model=list[TaskOut])
def get_tasks(
    sort: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tasks from projects owned by the user, with optional sorting"""
    tasks = (
        db.query(models.Task)
        .join(models.Project, models.Task.project_id == models.Project.id)
        .filter(models.Project.owner_id == current_user.id)
        .all()
    )

    if sort is None:
        return tasks

    task_dicts = [
        {
            "id": t.id,
            "title": t.title,
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date,
            "project_id": t.project_id,
        }
        for t in tasks
    ]

    # Apply sorting using insertion sort algorithm
    if sort == "priority":
        for t in task_dicts:
            t["_sort_key"] = PRIORITY_RANK.get(t["priority"], 0)
        insertion_sort(task_dicts, "_sort_key")
    elif sort == "due_date":
        for t in task_dicts:
            t["_sort_key"] = t["due_date"] or ""
        insertion_sort(task_dicts, "_sort_key")
    else:
        raise HTTPException(status_code=400, detail="Invalid sort parameter")

    return task_dicts

@app.get("/tasks/search")
def search_tasks(
    title: str,
    algo: str = "binary",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search tasks by title using specified algorithm (binary or linear)"""
    tasks = (
        db.query(models.Task)
        .join(models.Project, models.Task.project_id == models.Project.id)
        .filter(models.Project.owner_id == current_user.id)
        .all()
    )

    index = [{"id": t.id, "title": t.title} for t in tasks]

    if algo == "binary":
        insertion_sort(index, "title")
        idx = binary_search(index, title, "title")
    elif algo == "linear":
        idx = linear_search(index, title, "title")
    else:
        raise HTTPException(status_code=400, detail="Invalid algo parameter")

    if idx == -1:
        raise HTTPException(status_code=404, detail="Task not found")

    matched_id = index[idx]["id"]
    task = db.query(models.Task).filter(models.Task.id == matched_id).first()
    return task

@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific task by ID (must belong to user's project)"""
    task = (
        db.query(models.Task)
        .join(models.Project, models.Task.project_id == models.Project.id)
        .filter(models.Task.id == task_id, models.Project.owner_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing task"""
    task = (
        db.query(models.Task)
        .join(models.Project, models.Task.project_id == models.Project.id)
        .filter(models.Task.id == task_id, models.Project.owner_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a task"""
    task = (
        db.query(models.Task)
        .join(models.Project, models.Task.project_id == models.Project.id)
        .filter(models.Task.id == task_id, models.Project.owner_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

@app.get("/projects/{project_id}/stats")
def get_project_stats(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get statistics for a specific project"""
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id, models.Project.owner_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    total_tasks = (
        db.query(func.count(models.Task.id))
        .filter(models.Task.project_id == project_id)
        .scalar()
    )

    status_counts = (
        db.query(models.Task.status, func.count(models.Task.id))
        .filter(models.Task.project_id == project_id)
        .group_by(models.Task.status)
        .all()
    )

    status_breakdown = {"pending": 0, "in_progress": 0, "completed": 0}
    for s, count in status_counts:
        status_breakdown[s] = count

    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_tasks": total_tasks,
        "status_breakdown": status_breakdown
    }

# ===================================================================
# NOTIFICATIONS ENDPOINTS
# ===================================================================

@app.get("/notifications", response_model=list[NotificationOut])
def get_notifications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all notifications for the current user"""
    notifications = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )
    return notifications

@app.put("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a specific notification as read"""
    notif = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id, models.Notification.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

@app.post("/notifications/mark-all-read")
def mark_all_notifications_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for the current user"""
    (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id, models.Notification.is_read == False)
        .update({"is_read": True})
    )
    db.commit()
    return {"message": "All notifications marked as read"}

# ===================================================================
# CHAT ENDPOINT - AI Assistant via Groq API
# ===================================================================

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

CHAT_SYSTEM_PROMPT = (
    "You are TaskFlow's in-app help assistant. TaskFlow is a task and "
    "project management web app with these features: Dashboard (overview "
    "KPIs), Projects (create/browse projects with progress bars), Tasks "
    "(full CRUD, with a due date + time picker), Quick Add (type a plain-"
    "English sentence like 'Finish the report next Friday, it's urgent' and "
    "it auto-fills title/priority/due date), Search (exact task title "
    "search using binary or linear search), Sort (priority or due date, "
    "powered by insertion sort), Stats (per-project task counts by "
    "status), and Notifications (a bell icon showing recent activity). "
    "Answer questions about how to use these features concisely and "
    "practically. If asked something unrelated to TaskFlow, answer briefly "
    "and steer back to how TaskFlow can help."
)

@app.post("/chat", response_model=ChatResponse)
def chat_with_ai(
    payload: ChatRequest,
    current_user: models.User = Depends(get_current_user),
):
    """Chat with AI assistant for help using TaskFlow features"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Chat is not configured — GROQ_API_KEY is missing from the environment.",
        )

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": payload.message},
                ],
                "temperature": 0.5,
                "max_completion_tokens": 500,
            },
            timeout=20,
        )
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Could not reach the chat service.")

    if response.status_code != 200:
        logger.error(f"Groq API error {response.status_code}: {response.text}")
        raise HTTPException(status_code=502, detail="The chat service returned an error.")

    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    return ChatResponse(reply=reply)