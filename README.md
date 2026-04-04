# Finance Data Processing & Access Control Backend

> Built for the **Zorvyn FinTech Backend Developer Intern** assignment.

A production-structured REST API backend for a finance dashboard system featuring JWT authentication, role-based access control (RBAC), full financial record management, and aggregated analytics — built with **FastAPI + SQLAlchemy + SQLite**.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Setup & Run](#setup--run)
4. [Running Tests](#running-tests)
5. [API Reference](#api-reference)
6. [Role Permissions Matrix](#role-permissions-matrix)
7. [Data Models](#data-models)
8. [Design Decisions & Assumptions](#design-decisions--assumptions)
9. [Assignment Coverage](#assignment-coverage)

---

## Tech Stack

| Concern | Technology | Version |
|---|---|---|
| API Framework | FastAPI | 0.115.0 |
| Database ORM | SQLAlchemy | 2.0.35 |
| Database | SQLite (file-based) | built-in |
| Request Validation | Pydantic v2 | 2.9.2 |
| JWT Authentication | python-jose | 3.3.0 |
| Password Hashing | passlib[bcrypt] | 1.7.4 |
| Rate Limiting | slowapi | 0.1.9 |
| ASGI Server | Uvicorn | 0.30.6 |
| Testing | pytest + httpx | 8.3.3 / 0.27.2 |

---

## Project Structure

```
finance-backend/
├── app/
│   ├── main.py           # App factory, middleware, error handlers
│   ├── config.py         # Settings (loaded from .env or defaults)
│   ├── database.py       # SQLAlchemy engine + session factory
│   ├── models.py         # ORM models: User, FinancialRecord + enums
│   ├── schemas.py        # Pydantic schemas for request/response
│   ├── auth.py           # JWT creation/decoding + bcrypt hashing
│   ├── limiter.py        # Rate limiter instance (slowapi)
│   ├── dependencies.py   # get_current_user, require_role() RBAC factory
│   └── routers/
│       ├── auth.py       # POST /auth/login, GET /auth/me
│       ├── users.py      # CRUD /users  (Admin only)
│       ├── records.py    # CRUD /records with filters & pagination
│       └── dashboard.py  # /dashboard/* analytics endpoints
├── tests/
│   ├── conftest.py       # Shared fixtures: test DB, client, tokens
│   ├── test_auth.py      # 8  tests — login, tokens, /me
│   ├── test_users.py     # 12 tests — user CRUD & role guards
│   ├── test_records.py   # 16 tests — record CRUD, filters, validation
│   └── test_dashboard.py # 11 tests — analytics, trends, summaries
├── seed.py               # Populates DB with 3 users + 12 months of data
├── pytest.ini            # pytest configuration
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup & Run

### Prerequisites
- Python 3.10 or higher
- pip

### Step 1 — Unzip and enter the project

```bash
tar -xzf finance-backend.tar.gz
cd finance-backend
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — (Optional) Configure environment

```bash
cp .env.example .env
# Edit .env to change SECRET_KEY or DATABASE_URL
```

> The app works without a `.env` file using secure defaults.

### Step 5 — Seed the database

```bash
python seed.py
```

This creates 3 demo users and ~60 financial records across 12 months:

| Username | Password    | Role     |
|----------|-------------|----------|
| `admin`  | `admin123`  | admin    |
| `analyst`| `analyst123`| analyst  |
| `viewer` | `viewer123` | viewer   |

### Step 6 — Start the server

```bash
uvicorn app.main:app --reload
```

| URL | Description |
|-----|-------------|
| http://localhost:8000 | API root |
| http://localhost:8000/docs | **Swagger UI** (interactive) |
| http://localhost:8000/redoc | ReDoc documentation |
| http://localhost:8000/health | Health check |

### Step 7 — Try it out

1. Open http://localhost:8000/docs
2. Click **POST /auth/login** → **Try it out**
3. Enter `username: admin`, `password: admin123` → **Execute**
4. Copy the `access_token` from the response
5. Click the **🔒 Authorize** button at the top → paste the token
6. All endpoints are now unlocked

---

## Running Tests

```bash
pytest
```

Expected output:
```
tests/test_auth.py       ........   8 passed
tests/test_users.py      ............  12 passed
tests/test_records.py    ................  16 passed
tests/test_dashboard.py  ...........  11 passed
============== 47 passed in X.XXs ==============
```

Tests run against a **separate** `test_finance.db` — your production `finance.db` is never touched.

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/login` | Public | Login → JWT Bearer token *(rate limited: 10/min)* |
| `GET`  | `/auth/me` | Any | Current user profile |

### User Management

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `POST`   | `/users/`        | Admin | Create a user |
| `GET`    | `/users/`        | Admin | List users (filter: `role`, `is_active`) |
| `GET`    | `/users/{id}`    | Admin | Get user by ID |
| `PATCH`  | `/users/{id}`    | Admin | Update name, email, role, or status |
| `DELETE` | `/users/{id}`    | Admin | Delete user permanently |

### Financial Records

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `POST`   | `/records/`     | Admin | Create a record |
| `GET`    | `/records/`     | All   | List records (paginated + filtered) |
| `GET`    | `/records/{id}` | All   | Get record by ID |
| `PUT`    | `/records/{id}` | Admin | Update a record (partial) |
| `DELETE` | `/records/{id}` | Admin | Soft-delete a record |

**Filter query params:** `type`, `category`, `date_from`, `date_to`, `search`, `page`, `page_size`

### Dashboard Analytics

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| `GET` | `/dashboard/summary`    | All | Total income, expenses, net balance, counts |
| `GET` | `/dashboard/categories` | All | Totals grouped by category (filter: `type`, dates) |
| `GET` | `/dashboard/trends`     | All | Income vs expense by period (`granularity=monthly\|weekly`, `year`) |
| `GET` | `/dashboard/recent`     | All | N most recent records (`limit`, default 10, max 50) |

---

## Role Permissions Matrix

| Action | Viewer | Analyst | Admin |
|--------|:------:|:-------:|:-----:|
| Login | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| List & view records | ✅ | ✅ | ✅ |
| Filter & search records | ✅ | ✅ | ✅ |
| View dashboard analytics | ✅ | ✅ | ✅ |
| Create records | ❌ | ❌ | ✅ |
| Update records | ❌ | ❌ | ✅ |
| Delete records | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

---

## Data Models

### User
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer | Primary key |
| `username` | String(50) | Unique, alphanumeric + `-_` |
| `email` | String(100) | Unique, validated |
| `full_name` | String(100) | Optional |
| `hashed_password` | String | bcrypt hash, never plaintext |
| `role` | Enum | `viewer`, `analyst`, `admin` |
| `is_active` | Boolean | Default `True` |
| `created_at` | DateTime | Auto-set |
| `updated_at` | DateTime | Auto-updated |

### FinancialRecord
| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer | Primary key |
| `amount` | Float | Must be > 0 |
| `type` | Enum | `income` or `expense` |
| `category` | String(100) | e.g. "Salary", "Rent" |
| `date` | DateTime | ISO-8601 |
| `notes` | Text | Optional |
| `created_by` | FK → users.id | Tracks creator |
| `is_deleted` | Boolean | Soft-delete flag |
| `created_at` | DateTime | Auto-set |
| `updated_at` | DateTime | Auto-updated |

---

## Design Decisions & Assumptions

1. **SQLite over PostgreSQL** — chosen for zero-config local setup. Switching requires only changing `DATABASE_URL` in `.env` to a Postgres connection string; no application code changes needed.

2. **Soft delete** — records are never destroyed. Setting `is_deleted = True` hides them from all queries while preserving the audit trail in the database.

3. **Analyst role** — given the same read access as viewer in the current implementation. It is modeled as a separate role so it can be extended (e.g., export reports, create draft records) without a migration.

4. **JWT contains role** — the token payload includes both `user_id` and `role`. On every request, `get_current_user` re-fetches the user from the DB to ensure deactivated accounts are rejected in real time and the role hasn't changed.

5. **`require_role()` factory** — access control is expressed as a single dependency per endpoint (`Depends(require_admin)`) rather than inline `if` checks inside handler functions. This keeps business logic clean and makes permissions auditable in one file.

6. **Rate limiting on login** — the `/auth/login` endpoint is capped at 10 requests/minute per IP using `slowapi`. A `429 Too Many Requests` is returned when exceeded.

7. **Pagination hard cap** — `page_size` is capped at 100 to prevent expensive unbounded queries from reaching the database.

8. **Dashboard uses server-side aggregation** — `SUM`, `COUNT`, and `strftime` grouping are performed in SQL, not Python, so analytics endpoints stay efficient as the dataset grows.

9. **Test isolation** — the test suite uses a completely separate `test_finance.db` via FastAPI's dependency override mechanism, so tests never touch the production database.
