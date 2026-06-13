# PulseIQ Backend

PulseIQ is a FastAPI backend for a multi-tenant facility intelligence system. It lets facility teams submit operational messages, extracts timeline events from those messages, resolves related entities, and answers natural-language questions with supporting sources and confidence scoring.

## Tech Stack

- FastAPI and Uvicorn
- PostgreSQL with `pgvector`
- SQLAlchemy async ORM and Alembic migrations
- Redis
- Ollama-backed local LLM calls
- JWT authentication with role-based access control

## Project Structure

```text
pulseiq_backend/
├── api/routes/          # FastAPI route handlers
├── core/                # config, database, security, logging
├── db/migrations/       # Alembic migrations
├── models/              # SQLAlchemy models
├── repositories/        # database access helpers
├── schemas/             # Pydantic request/response schemas
├── services/            # LLM, retrieval, extraction, timeline, audit logic
├── docs/                # frontend API docs/contracts
├── main.py              # FastAPI app entrypoint
└── requirements.txt
```

## Prerequisites

- Python 3.11+
- Docker Desktop, for PostgreSQL/Redis/Ollama services
- Ollama model available locally in the Ollama container or host service

## Environment Variables

Create a `.env` file in this folder:

```env
DATABASE_URL=postgresql+asyncpg://pulseiq:pulseiq@localhost:5432/pulseiq
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_FALLBACK_MODEL=llama2
SECRET_KEY=replace-with-a-long-random-secret
SUPER_ADMIN_SETUP_TOKEN=replace-with-a-bootstrap-token
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Setup

From the `pulseiq_backend` folder:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Start the supporting services:

```bash
docker compose up -d db redis ollama
```

Apply database migrations:

```bash
PYTHONPATH=.. alembic upgrade head
```

## Start the API

From the `pulseiq_backend` folder:

```bash
PYTHONPATH=.. uvicorn pulseiq_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or from the parent folder:

```bash
uvicorn pulseiq_backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Main API Flow

1. Bootstrap the first super admin:

```http
POST /auth/bootstrap-super-admin
```

Body:

```json
{
  "email": "admin@example.com",
  "password": "a-strong-password",
  "setup_token": "your-super-admin-setup-token"
}
```

2. Log in:

```http
POST /auth/login
```

This uses OAuth2 form data with `username` and `password`, and returns a bearer token.

3. Create a facility as a super admin:

```http
POST /tenants
```

4. Create a facility admin as a super admin:

```http
POST /users/facility-admins
```

5. Create employees as a facility admin:

```http
POST /users/employees
```

Body:

```json
{
  "email": "employee@example.com",
  "department": "engineering"
}
```

Use `GET /users/employee-departments` to populate the department dropdown. The `role` field is reserved for app permissions; use `department` for job area values such as `sales`, `engineering`, or `operations`.

6. Submit facility messages as an authenticated user:

```http
POST /messages
```

Body:

```json
{
  "content": "Resident John reported dizziness at 10 AM and nurse Amy checked vitals."
}
```

7. Ask questions over the facility timeline:

```http
POST /query
```

Body:

```json
{
  "question": "What happened with John today?"
}
```

## Useful Commands

```bash
# activate virtual environment
source venv/bin/activate

# start database, redis, and ollama
docker compose up -d db redis ollama

# run migrations
PYTHONPATH=.. alembic upgrade head

# start backend from this folder
PYTHONPATH=.. uvicorn pulseiq_backend.main:app --reload --host 0.0.0.0 --port 8000

# check health
curl http://localhost:8000/health
```

## Notes

- The code imports modules using the `pulseiq_backend` package name, so running commands from inside this folder requires `PYTHONPATH=..`.
- `docker-compose.yml` defines `db`, `redis`, `ollama`, and `api`, but there is no `Dockerfile` in this repo right now. Use `docker compose up -d db redis ollama` for local dependencies unless you add a Dockerfile for the API service.
- Users with `must_reset_password=true` must call `POST /auth/reset-password` before submitting messages.
