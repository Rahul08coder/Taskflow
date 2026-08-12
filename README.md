# TaskFlow

A full-stack task and project management platform — FastAPI + SQLAlchemy backend (Supabase/Postgres) with a vanilla HTML/CSS/JS dashboard. Built across three graded sections (Core App, Algorithms Engine, AI Quick-Add), plus several extra features layered on top (see [Extra Features](#extra-features-beyond-the-original-brief) at the bottom).

---

## ⚠️ Read this first — the API requires authentication

Every data endpoint in this API (`/projects`, `/tasks`, `/tasks/search`, `/tasks/quick-add`, `/projects/{id}/stats`) requires a login token. This was added as an extra feature on top of the original brief — the brief itself does not require or forbid authentication, and every acceptance criterion below still holds, but you must **register and log in first** before exercising any endpoint. There is no way to call the CRUD/algorithms/quick-add endpoints anonymously.

**The 3-step flow every grader/tester needs:**

1. **Register** a user — `POST /auth/register` (any email works, no verification step)
2. **Log in** with that user — `POST /auth/login` — returns a `token`
3. **Send that token** on every subsequent request as a header: `Authorization: Bearer <token>`

Full request/response examples are in the [Authentication](#authentication-extra-feature) section and repeated inline for every endpoint below.

One consequence worth knowing: because every project/task now belongs to whichever user is logged in, **a brand-new account starts with an empty dashboard** — zero projects, zero tasks — until that user creates their own. This is intentional (per-user data isolation), not a bug.

---

## Repository Structure

```
Taskflow/
├── backend/
│   ├── database.py            # DB engine + session dependency (get_db)
│   ├── models.py               # SQLAlchemy models: User, Project, Task, Notification
│   ├── schemas.py              # Pydantic schemas (Create/Update/Out/Auth/Chat/Notification)
│   ├── main.py                  # FastAPI app — every endpoint lives here
│   ├── auth_utils.py            # Password hashing + session token generation (stdlib only)
│   ├── algorithms.py            # insertion_sort, binary_search, linear_search
│   │                             # + comparison-counting wrapper versions
│   ├── quick_add_parser.py      # Deterministic rule-based mock parser (Section 3)
│   ├── benchmark.py             # Section 2 benchmark script (3 data sizes)
│   ├── benchmark_results.txt    # Raw comparison-count output from benchmark.py
│   ├── check_algorithms.py      # Section 2 PASS/FAIL checks script
│   ├── create_tables.py         # One-time / incremental DB table creation script
│   ├── test_connection.py       # DB connectivity sanity check
│   └── requirements.txt
└── frontend/
    ├── index.html                # Main dashboard (requires login)
    ├── login.html                 # Login page
    ├── register.html              # Registration page
    ├── styles.css
    └── app.js
```

---

## Environment Setup

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
```

### Environment variables (`.env` file, inside `backend/`)

```dotenv
DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>:<port>/<database>
GROQ_API_KEY=your_free_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

| Variable | Required? | Purpose |
|---|---|---|
| `DATABASE_URL` | **Yes** | Supabase Postgres connection string. Uses `postgresql+psycopg://` (psycopg v3), not `psycopg2` — needed for compatibility with newer Python versions. |
| `GROQ_API_KEY` | No — only for the chatbot | Free-tier key from [console.groq.com](https://console.groq.com). Without it, every other feature works normally; only `POST /chat` returns a graceful `503`. |
| `GROQ_MODEL` | No | Defaults to `openai/gpt-oss-20b` if unset. |

### Creating the database tables

```powershell
python create_tables.py
```

This is safe to re-run — SQLAlchemy's `create_all()` only creates tables that don't already exist; it never touches or drops existing ones.

---

## Running the App Locally (Two-Process Setup)

**1. Start the backend** (from `backend/`, with the venv active):
```powershell
uvicorn main:app --reload
```
Runs at `http://127.0.0.1:8000`. Interactive API docs at `http://127.0.0.1:8000/docs`.

**2. Serve the frontend** — from `frontend/`, using any static server on a different port (e.g. VS Code's Live Server on port `5500`).

The backend's CORS config in `main.py` explicitly allows `http://127.0.0.1:5500` and `http://localhost:5500`. If you serve the frontend from a different port, update the `allow_origins` list in `main.py` to match.

**3. Open the frontend, register, log in** — `register.html` → `login.html` → `index.html`.

---

## Database Schema

Three required tables (`users`, `projects`, `tasks`) plus one extra table (`notifications`) added for the notifications feature.

| Table | Columns | Constraints |
|---|---|---|
| **users** | `id` (PK), `email`, `name`, `password_hash`, `session_token`, `is_admin`, `created_at` | `email` UNIQUE + NOT NULL, `name` NOT NULL |
| **projects** | `id` (PK), `name`, `owner_id` | `owner_id` FK → `users.id`, `name` NOT NULL |
| **tasks** | `id` (PK), `title`, `priority`, `status`, `due_date`, `project_id` | `project_id` FK → `projects.id`, `title` NOT NULL, `priority` CHECK IN `('low','medium','high')`, `status` CHECK IN `('pending','in_progress','completed')` |
| **notifications** *(extra)* | `id` (PK), `user_id`, `message`, `type`, `is_read`, `created_at` | `user_id` FK → `users.id` |

`User.projects` ↔ `Project.owner` and `Project.tasks` ↔ `Task.project` are wired with `relationship()` + `back_populates` on both sides in `models.py`.

`password_hash`, `session_token`, and `is_admin` on `users`, and the entire `notifications` table, are **not required by the original brief** — they exist to support the extra authentication/admin/notifications features described at the bottom of this README.

---

## Full Endpoint List

Every endpoint below except `/auth/register` and `/auth/login` requires the header:
```
Authorization: Bearer <token>
```

### Authentication *(extra feature)*

**`POST /auth/register`** — create an account. Any email is accepted, no verification.

Request:
```json
{ "name": "Rahul", "email": "rahul@example.com", "password": "at-least-6-chars" }
```
Response `201`:
```json
{ "id": 1, "email": "rahul@example.com", "name": "Rahul" }
```

**`POST /auth/login`** — exchange email/password for a session token.

Request:
```json
{ "email": "rahul@example.com", "password": "at-least-6-chars" }
```
Response `200`:
```json
{ "token": "a94f...64-char-hex...", "user_id": 1, "name": "Rahul", "email": "rahul@example.com", "is_admin": false }
```
The token has **no expiry** — it stays valid until `/auth/logout` is called (or the user logs in elsewhere, which issues a new token and invalidates the old one).

**`POST /auth/logout`** — invalidate the current session token.

Response `200`:
```json
{ "message": "Logged out successfully" }
```

---

### Users

**`POST /users`** — legacy unauthenticated user creation, kept for backward compatibility with early testing. Not used by the frontend; prefer `/auth/register`.

**`GET /users`** — *admin-only* (see [Admin](#admin-panel-extra-feature) below). Returns the raw list of all users. Regular users get `403`.

---

### Projects — owner-scoped

**`POST /projects`** — create a project. `owner_id` is **not** in the request body; it's taken automatically from the logged-in user's token.

Request:
```json
{ "name": "Website Redesign" }
```
Response `201`:
```json
{ "id": 1, "name": "Website Redesign", "owner_id": 1 }
```

**`GET /projects`** — list only the current user's own projects.

Response `200`:
```json
[ { "id": 1, "name": "Website Redesign", "owner_id": 1 } ]
```

Failure case: creating a project with a blank name → `422` (Pydantic validator rejects it).

---

### Tasks — full CRUD, owner-scoped

**`POST /tasks`**

Request:
```json
{ "title": "Design homepage mockup", "priority": "high", "status": "pending", "due_date": "2026-08-20", "project_id": 1 }
```
Response `201`:
```json
{ "id": 1, "title": "Design homepage mockup", "priority": "high", "status": "pending", "due_date": "2026-08-20", "project_id": 1 }
```
Failure case: `project_id` that doesn't exist (or belongs to someone else) → `404`. Blank `title` → `422`.

**`GET /tasks`** — list the current user's tasks. Optional `?sort=priority` or `?sort=due_date` (see [Algorithms](#algorithms-engine)).

**`GET /tasks/{task_id}`** — get one task. Not found (or not yours) → `404`.

**`PUT /tasks/{task_id}`** — partial update (only send the fields you want to change).

Request:
```json
{ "status": "completed" }
```
Response `200`: full updated task object.

**`DELETE /tasks/{task_id}`**

Response `200`:
```json
{ "message": "Task deleted successfully" }
```

---

### Stats

**`GET /projects/{project_id}/stats`** — per-project task count and status breakdown, computed with `COUNT` + `GROUP BY` inside the SQL query (not aggregated in Python).

Response `200`:
```json
{
  "project_id": 1,
  "project_name": "Website Redesign",
  "total_tasks": 3,
  "status_breakdown": { "pending": 1, "in_progress": 1, "completed": 1 }
}
```
Verified against two projects with different task counts during development (3 tasks vs. 2 tasks) — numbers matched manual counts exactly.

---

## Algorithms Engine

Two endpoints powered by hand-rolled `insertion_sort`, `binary_search`, and `linear_search` in `algorithms.py` — no built-in `sorted()`/`list.sort()` anywhere in this path. Not-found is represented as `-1`.

**`GET /tasks?sort=priority`** and **`GET /tasks?sort=due_date`** — fetches this user's tasks, maps priority to a numeric rank (`low=1, medium=2, high=3`) when sorting by priority, then sorts with `insertion_sort` before returning JSON.

**`GET /tasks/search?title=<exact title>&algo=binary|linear`** (default `binary`) — builds an in-memory `{id, title}` index from this user's real tasks, sorts it with `insertion_sort` and locates the match with `binary_search` (or scans unsorted with `linear_search`).

Response `200` (task found) or `404`:
```json
{ "detail": "Task not found" }
```

### Time Complexity

| Algorithm | Best Case | Worst Case |
|---|---|---|
| `insertion_sort` | O(n) — already sorted | O(n²) — reverse sorted |
| `binary_search` | O(1) — target at the middle | O(log n) |
| `linear_search` | O(1) — target at the start | O(n) |

### Benchmark Results

Measured with `benchmark.py` using synthetic in-memory task dicts (same fields the real endpoints use), reproducible with `random.seed(42)`. Raw numbers also saved in `benchmark_results.txt`.

| Size | insertion_sort (by priority) | insertion_sort (by title) | binary_search | linear_search |
|---|---|---|---|---|
| 10 | 28 | 31 | 3 | 6 |
| 500 | 42,245 | 59,971 | 9 | 251 |
| 3,000 | 1,521,369 | 2,267,956 | 11 | 1,501 |

Run it yourself: `python benchmark.py`

### Is Sorting-First Worth It?

The comparison counts show two very different growth curves. Insertion sort's cost grows roughly quadratically — going from 10 to 3,000 tasks (a 300x increase in size) pushed comparisons up by more than 50,000x (28 → 1.5M+ for a priority sort). Binary search, by contrast, barely moves: the same 300x size increase only took comparisons from 3 to 11, confirming its logarithmic behavior. Linear search sits in between, scaling roughly linearly with size (6 → 1,501, tracking size almost 1:1).

Given how TaskFlow is actually used — a team viewing and re-sorting their task list many times a day, but adding or renaming tasks comparatively rarely — paying the O(n²) sort cost on every single `GET /tasks?sort=priority` call is not efficient at scale. At 3,000 tasks, resorting from scratch on every page load costs over a million comparisons each time, even though the underlying data barely changed between requests. It would be more efficient to sort once and cache the result (or maintain sorted order incrementally on insert), only re-sorting when a task's priority actually changes. Search, however, tells the opposite story: binary search's near-flat cost curve makes the one-time O(n log n) cost of keeping an index sorted for search purposes cheap and clearly worth it compared to linear search's O(n) blowup, especially as the task list grows.

### Automated Checks

```powershell
python check_algorithms.py
```
Prints one `PASS`/`FAIL` line per case (empty-list sort, single-element sort, binary search at first/last/middle index, not-found case, counting-wrapper correctness). All 10 checks currently `PASS`.

---

## AI Quick-Add

**`POST /tasks/quick-add`** — accepts `{"description": "<free text>", "project_id": <int>}`, creates a real task row using the **required, keyless, deterministic mock parser** (`quick_add_parser.py`) — zero network calls, zero API keys. The endpoint still builds a role-based `system`/`user` message pair before parsing, so the code stays structured the same way whether the mock or a real LLM answers it.

Request:
```json
{ "description": "Finish the report next Friday, it's urgent", "project_id": 1 }
```
Response `201`:
```json
{ "id": 5, "title": "Finish the report , it's", "priority": "high", "status": "pending", "due_date": "next friday", "project_id": 1 }
```
Failure case: `project_id` that doesn't exist (or isn't yours) → `422`, no row written.

### Prompting Technique

The system message is modeled on **zero-shot prompting**: it states the extraction task and the exact output fields directly, without embedding worked examples in the message itself. This fits a keyless, deterministic mock, since the actual parsing logic is rule-based rather than inferred by a model reading examples — there's no in-context learning happening, so few-shot examples in the prompt would add token cost without changing the mock's behavior at all. Chain-of-thought was also not used: the extraction is a fixed lookup-and-strip procedure (checked keyword groups, in a fixed order), not a multi-step reasoning task that benefits from an explicit "think step by step" trace, and asking for visible reasoning would only inflate token usage for no accuracy gain here.

If this endpoint's optional real-LLM path were ever enabled (`USE_REAL_LLM=true`), the same zero-shot system message would still be the right starting point for a real model, since the extraction rules are simple, closed-vocabulary, and unambiguous enough that a model shouldn't need worked examples to follow them reliably — few-shot would mainly become useful if the real model started missing edge cases (like the group-priority-wins rule, or multi-occurrence keyword stripping) that examples could disambiguate. For now, with the mock as the graded path, zero-shot keeps the prompt short and keeps response reliability entirely in the hands of the deterministic code rather than a model's interpretation.

### Example Descriptions and Parsed Output

Computed by running the Task 3 algorithm exactly as specified — verifiable by calling `POST /tasks/quick-add` with the same `description` values.

| # | Input Description | Parsed Output |
|---|---|---|
| 1 | `Call the client whenever you get a chance` | `{"title": "Call the client you get a chance", "priority": "low", "due_date_hint": null}` |
| 2 | `Prepare slides for the demo, ASAP` | `{"title": "Prepare slides for the demo,", "priority": "high", "due_date_hint": null}` |
| 3 | `Submit the report by next Wednesday` | `{"title": "Submit the report by", "priority": "medium", "due_date_hint": "next wednesday"}` |
| 4 | `Water the plants` | `{"title": "Water the plants", "priority": "medium", "due_date_hint": null}` |
| 5 | `Renew the domain, low priority, whenever works` | `{"title": "Renew the domain, , works", "priority": "low", "due_date_hint": null}` |
| 6 | `Fix the login bug today, it is urgent` | `{"title": "Fix the login bug , it is", "priority": "high", "due_date_hint": "today"}` |

`USE_REAL_LLM` is not implemented — the mock is the only path, so grading with no API key present works with zero configuration.

---

## Extra Features (beyond the original brief)

These were built on top of the three graded sections as personal additions. **None of them are required for grading** — every acceptance criterion above is satisfied with or without them — but they're documented here for completeness.

### Authentication
Register/login/logout with persistent session tokens (not JWT — no expiry, invalidated only by logout or a fresh login). Passwords are hashed with PBKDF2-HMAC-SHA256 (`auth_utils.py`, stdlib only — `bcrypt` was deliberately avoided due to prebuilt-wheel availability problems on newer Python versions). Every project/task is scoped to its owner.

### Admin Panel
Accounts with `is_admin = true` (set manually in the database — there's no self-service way to become admin) get access to:
- **`GET /admin/users`** — every registered user's name/email + project/task **counts** (never their actual content)
- **`GET /admin/users/{user_id}/detail`** — drill into one specific user's actual projects and tasks (admin-only; a `403` is returned to anyone else)

### Notifications
A `notifications` table auto-populated when a task/project is created, quick-add is used, or a new user registers (admins are notified of new registrations). Endpoints: `GET /notifications`, `PUT /notifications/{id}/read`, `POST /notifications/mark-all-read`. Surfaced in the frontend as a bell icon with an unread-count badge.

### AI Help Chatbot
**`POST /chat`** — `{"message": "<question>"}` → forwards to Groq's free-tier API (`openai/gpt-oss-20b` by default, configurable via `GROQ_MODEL`) with a system prompt describing TaskFlow's features, for an in-app help assistant. Requires `GROQ_API_KEY`; without it, returns a graceful `503` rather than crashing. Surfaced in the frontend as a floating chat widget.

---

## Git Workflow

Developed across multiple feature branches, each committed to at least twice and merged into `main` with `--no-ff` (visible via `git log --graph --all`): `feature/frontend-dashboard`, `feature/algorithms-engine`, `feature/ai-quick-add`, and the auth/notifications/chatbot work.