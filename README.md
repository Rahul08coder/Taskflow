# Taskflow

A task management app — FastAPI + SQLAlchemy backend (Supabase/Postgres) with a vanilla HTML/CSS/JS frontend.

## Project Structure

```
Taskflow/
├── backend/
│   ├── database.py           # DB engine + session dependency
│   ├── models.py              # SQLAlchemy models (User, Project, Task)
│   ├── schemas.py             # Pydantic schemas (Create/Update/Out/QuickAdd)
│   ├── main.py                 # FastAPI app — all endpoints (CRUD, stats,
│   │                            # sort/search, quick-add)
│   ├── algorithms.py           # insertion_sort, binary_search, linear_search
│   │                            # + comparison-counting wrapper versions
│   ├── quick_add_parser.py     # deterministic rule-based mock parser (Section 3)
│   ├── benchmark.py            # Section 2 benchmark script (3 data sizes)
│   ├── benchmark_results.txt   # raw comparison-count output from benchmark.py
│   ├── check_algorithms.py     # Section 2 PASS/FAIL checks script
│   ├── create_tables.py        # one-time DB table creation script
│   ├── test_connection.py      # DB connectivity sanity check
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── styles.css
    └── script.js
```

`seed.py`-equivalent functionality (generating benchmark test data) lives inside `benchmark.py` itself, which generates synthetic in-memory task data at three sizes rather than requiring a separate seeding step — see the Algorithms Engine section below for details.

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

## Algorithms Engine (Section 2)

Two additional endpoints are powered by hand-rolled `insertion_sort`, `binary_search`, and `linear_search` implementations in `algorithms.py` — no built-in `sorted()`/`list.sort()` is used anywhere in this path. Not-found results are represented as `-1`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/tasks?sort=priority` | Returns tasks sorted by priority (low→high), via `insertion_sort` on real DB rows |
| GET | `/tasks?sort=due_date` | Returns tasks sorted by due date, via `insertion_sort` |
| GET | `/tasks/search?title=<exact title>&algo=binary\|linear` | Finds a task by exact title using `binary_search` (default) or `linear_search` over an in-memory index built from real DB rows |

### Time Complexity

| Algorithm | Best Case | Worst Case |
|---|---|---|
| `insertion_sort` | O(n) — already sorted | O(n²) — reverse sorted |
| `binary_search` | O(1) — target at the middle | O(log n) |
| `linear_search` | O(1) — target at the start | O(n) |

### Benchmark Results

Measured with `benchmark.py` using synthetic in-memory task dicts (same fields the real endpoints use: `title`, `priority`, `due_date`), reproducible with `random.seed(42)`. Raw numbers also saved in `benchmark_results.txt`.

| Size | insertion_sort (by priority) | insertion_sort (by title) | binary_search | linear_search |
|---|---|---|---|---|
| 10 | 28 | 31 | 3 | 6 |
| 500 | 42,245 | 59,971 | 9 | 251 |
| 3,000 | 1,521,369 | 2,267,956 | 11 | 1,501 |

Run it yourself:
```bash
python benchmark.py
```

### Is Sorting-First Worth It?

The comparison counts show two very different growth curves. Insertion sort's cost grows roughly quadratically — going from 10 to 3,000 tasks (a 300x increase in size) pushed comparisons up by more than 50,000x (28 → 1.5M+ for a priority sort). Binary search, by contrast, barely moves: the same 300x size increase only took comparisons from 3 to 11, confirming its logarithmic behavior. Linear search sits in between, scaling roughly linearly with size (6 → 1,501, tracking size almost 1:1).

Given how TaskFlow is actually used — a team viewing and re-sorting their task list many times a day, but adding or renaming tasks comparatively rarely — paying the O(n²) sort cost on every single `GET /tasks?sort=priority` call is not efficient at scale. At 3,000 tasks, resorting from scratch on every page load costs over a million comparisons each time, even though the underlying data barely changed between requests. It would be more efficient to sort once and cache the result (or maintain sorted order incrementally on insert), only re-sorting when a task's priority actually changes. Search, however, tells the opposite story: binary search's near-flat cost curve makes the one-time O(n log n) cost of keeping an index sorted for search purposes cheap and clearly worth it compared to linear search's O(n) blowup, especially as the task list grows.

## AI Quick-Add (Section 3)

`POST /tasks/quick-add` accepts `{"description": "<free text>", "project_id": <int>}` and creates a real task row from it. Field extraction is done by a **required, keyless, deterministic rule-based mock parser** (`quick_add_parser.py`) — zero network calls, zero API keys, and it's what the endpoint uses by default. The endpoint still builds a role-based `system`/`user` message pair before parsing, so the code stays structured the same way whether the mock or a real LLM answers it.

### Prompting Technique

The system message is modeled on **zero-shot prompting**: it states the extraction task and the exact output fields directly ("extract a title, a priority of exactly low/medium/high, and a due-date hint"), without embedding worked examples in the message itself. This fits a keyless, deterministic mock, since the actual parsing logic is rule-based rather than inferred by a model reading examples — there's no in-context learning happening, so few-shot examples in the prompt would add token cost without changing the mock's behavior at all. Chain-of-thought was also not used: the extraction is a fixed lookup-and-strip procedure (checked keyword groups, in a fixed order), not a multi-step reasoning task that benefits from an explicit "think step by step" trace, and asking for visible reasoning would only inflate token usage for no accuracy gain here.

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

## Git Workflow

Developed on a feature branch, committed incrementally, merged into `main`.