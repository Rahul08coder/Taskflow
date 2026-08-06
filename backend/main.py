from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Task

from algorithms import insertion_sort, binary_search, linear_search
from typing import Optional
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}

import time
import logging

from fastapi.middleware.cors import CORSMiddleware

from database import get_db
import models
from schemas import TaskCreate, TaskUpdate, TaskOut, UserCreate, UserOut, ProjectCreate, ProjectOut

app = FastAPI(title="Taskflow API")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("taskflow")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000

    logger.info(
        f"{request.method} {request.url.path} - {process_time_ms:.2f}ms"
    )
    return response


@app.get("/")
def read_root():
    return {"message": "Taskflow API is running"}


@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(email=user.email, name=user.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users", response_model=list[UserOut])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@app.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == project.owner_id).first()
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_project = models.Project(name=project.name, owner_id=project.owner_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@app.get("/projects", response_model=list[ProjectOut])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return projects



@app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
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
    return new_task


@app.get("/tasks", response_model=list[TaskOut])
def get_tasks(sort: Optional[str] = None, db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()

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
def search_tasks(title: str, algo: str = "binary", db: Session = Depends(get_db)):
    tasks = db.query(models.Task).all()

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
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task





@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}


@app.get("/projects/{project_id}/stats")
def get_project_stats(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
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