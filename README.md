# TaskFlow

TaskFlow is a full-stack task and project management platform built with **FastAPI, SQLAlchemy, Supabase/PostgreSQL, and Vanilla HTML/CSS/JavaScript**.

It provides project management, task CRUD, authentication, admin monitoring, notifications, task-search/sorting algorithms, AI-style Quick-Add, and an optional help chatbot.

---

## Features

- User registration, login, and logout
- Secure password hashing and session-based authentication
- Project creation and user-specific project isolation
- Complete task CRUD:
  - Create
  - Read
  - Update
  - Delete
- Task priority and status management
- Project-wise task statistics
- Task sorting using **Insertion Sort**
- Task searching using **Binary Search** and **Linear Search**
- AI Quick-Add for converting natural-language task descriptions into structured tasks
- Notifications with unread count
- Admin panel for monitoring users, projects, and tasks
- Optional AI Help Chatbot using Groq
- Supabase/PostgreSQL database

---

## Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

### Database
- Supabase PostgreSQL

### Optional AI
- Groq API

---

## Project Structure

```text
TaskFlow/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth_utils.py
│   ├── algorithms.py
│   ├── quick_add_parser.py
│   ├── create_tables.py
│   ├── benchmark.py
│   ├── check_algorithms.py
│   ├── test_connection.py
│   └── requirements.txt
│
└── frontend/
    ├── index.html
    ├── login.html
    ├── register.html
    ├── styles.css
    └── app.js
```

---

## Environment Setup

Open PowerShell in the project folder:

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```env
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:<port>/<database>

# Optional - only required for the AI Help Chatbot
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

### Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection |
| `GROQ_API_KEY` | No | Enables the AI Help Chatbot |
| `GROQ_MODEL` | No | Groq model used by the chatbot |

---

## Database Setup

After configuring the Supabase connection:

```powershell
python create_tables.py
```

This creates the required database tables without deleting existing data.

### Main Tables

- `users`
- `projects`
- `tasks`
- `notifications`

---

## Run the Application

### 1. Start Backend

From the `backend/` directory:

```powershell
uvicorn main:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

API documentation:

```
http://127.0.0.1:8000/docs
```

### 2. Start Frontend

Open the `frontend/` folder with a static server such as VS Code Live Server.

Example:

```
http://127.0.0.1:5500
```

Then open:

```
register.html → login.html → index.html
```


---

## Main API Endpoints

### Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login |
| POST | `/auth/logout` | Logout |

### Projects

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/projects` | Create project |
| GET | `/projects` | Get user's projects |
| GET | `/projects/{project_id}/stats` | Project task statistics |

### Tasks

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/tasks` | Create task |
| GET | `/tasks` | Get user's tasks |
| GET | `/tasks/{task_id}` | Get one task |
| PUT | `/tasks/{task_id}` | Update task |
| DELETE | `/tasks/{task_id}` | Delete task |
| GET | `/tasks/search` | Search tasks |
| POST | `/tasks/quick-add` | Create task from natural language |

### Notifications

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/notifications` | Get notifications |
| PUT | `/notifications/{id}/read` | Mark notification as read |
| POST | `/notifications/mark-all-read` | Mark all as read |



The admin panel allows authorized admins to:

- View registered users
- View project/task counts
- Open detailed user information
- Monitor projects and tasks

### Admin Login Credentials

Use the following account to access the admin panel:

```
Email: Rahulsinghsnd12345@gmail.com
Password: Rahul2002
```

**Security note:** These credentials are included because they are provided as the demo/admin credentials for this project. Do not keep real production credentials in a public GitHub repository. Change the password before production deployment.

---

Run the algorithm checks:

```powershell
python check_algorithms.py
```

Run the benchmark:

```powershell
python benchmark.py
```

---

## AI Quick-Add

Quick-Add allows users to enter a task in natural language, for example:

```
Finish the report next Friday, it's urgent
```

The system extracts information such as:

- Task title
- Priority
- Due-date hint
- Project

The current graded Quick-Add implementation uses a **deterministic rule-based parser**, so it does not require an external AI API key.

---

## Database Relationships

```
User
 ├── Projects
 │    └── Tasks
 └── Notifications
```

- A user can own multiple projects.
- A project can contain multiple tasks.
- Tasks belong to a project.
- Notifications belong to a user.

---

## API Documentation

When the backend is running, FastAPI provides interactive API documentation at:

```
http://127.0.0.1:8000/docs
```

Use this page to test API endpoints directly.

---

## Important Notes

- Configure `DATABASE_URL` before starting the backend.
- Create database tables with `python create_tables.py`.
- Protected endpoints require a valid login token.
- A new user starts with an empty dashboard.
- `GROQ_API_KEY` is optional; it is only required for the chatbot.
- Do not commit `.env` files or real production credentials to GitHub.
