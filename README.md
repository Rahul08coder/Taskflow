# Taskflow

A task management app — FastAPI + SQLAlchemy backend (Supabase/Postgres) with a vanilla HTML/CSS/JS frontend.

## Project Structure

```
Taskflow/
├── backend/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
└── frontend/
    ├── index.html
    ├── styles.css
    └── script.js
```

## Running the App Locally (Two-Process Setup)

This project runs as two separate local processes: the FastAPI backend and a static file server for the frontend.

### 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file (or configure `database.py`) with your Supabase Session Pooler connection string.

Start the backend:

```bash
uvicorn main:app --reload
```

The backend runs at `http://127.0.0.1:8000`. API docs available at `http://127.0.0.1:8000/docs`.

### 2. Frontend setup

Serve the `frontend/` folder with any static server on a **different port**, e.g. VS Code's Live Server extension on port `5500`.

Open `index.html` via that server — it will load at `http://127.0.0.1:5500` (or `http://localhost:5500`).

> The backend's CORS config (in `main.py`) explicitly allows `http://127.0.0.1:5500` and `http://localhost:5500` as origins. If you serve the frontend from a different port, update the CORS `allow_origins` list in `main.py` to match.

### 3. Verify it's working

With both processes running, open the frontend URL in your browser. It should:
- Load the existing task list from the backend on page load
- Let you add, edit, and delete tasks — changes hit the real backend and persist on reload
- Show a validation message if you try to submit a task with an empty title
- Adapt its layout at 900px and 600px breakpoints

## Database Schema

- **users** — id (PK), name, email
- **projects** — id (PK), name, owner_id (FK → users.id)
- **tasks** — id (PK), title, priority, status, due_date, project_id (FK → projects.id)

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/tasks` | List all tasks |
| POST | `/tasks` | Create a task |
| PUT | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |
| GET | `/projects` | List projects |
| POST | `/projects` | Create a project |
| GET | `/projects/{id}/stats` | Task counts by status for a project |
| GET | `/users` | List users |
| POST | `/users` | Create a user |

## Git Workflow

Developed on a feature branch, committed incrementally, merged into `main`.

## Testing Verification

- Full CRUD tested end-to-end via PowerShell `Invoke-RestMethod` against the live Supabase-backed API.
- Stats endpoint (`GET /projects/{id}/stats`) verified against two test projects with different task counts and statuses — response numbers matched manual counts exactly.
- Frontend dashboard tested for add/edit/delete, empty-title validation, localStorage cache-then-fetch on load, and layout changes at both 900px and 600px breakpoints.