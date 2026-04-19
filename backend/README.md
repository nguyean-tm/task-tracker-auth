# Task Tracker — Backend

FastAPI + SQLAlchemy (async) + Alembic + PostgreSQL. JWT auth via python-jose, bcrypt via passlib.

## Quick start (local)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # fill in DATABASE_URL + SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000/docs
```

## Quick start (Docker)

```bash
# from repo root
cp backend/.env.example backend/.env   # edit values
docker compose up --build
```

Alembic runs automatically before uvicorn inside the container.

## Run tests

Tests use SQLite in-memory — no Postgres required.

```bash
cd backend
pytest -v
```

## API surface

| Method | Path            | Auth    | Description              |
|--------|-----------------|---------|--------------------------|
| POST   | /auth/register  | —       | Create account → 201     |
| POST   | /auth/login     | —       | Get JWT → 200            |
| GET    | /auth/me        | Bearer  | Current user → 200       |
| GET    | /healthz        | —       | Liveness probe           |

### Error codes

| Code | Reason                                   |
|------|------------------------------------------|
| 409  | Email already registered                 |
| 422  | Malformed email or password < 8 chars    |
| 401  | Bad credentials / missing / expired JWT  |

## Alembic migration notes

Migration `0001` creates the `users` table with `gen_random_uuid()` as the
server-side default for `id`. Downgrade drops the table cleanly.

```bash
alembic upgrade head    # apply
alembic downgrade base  # rollback everything
```
