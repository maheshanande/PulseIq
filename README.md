# PulseIQ

### Transforming Operational Chatter into Business Intelligence

PulseIQ is an AI-powered operational intelligence platform for SMEs, manufacturers, traders, distributors, and facility teams.

Businesses generate hundreds of operational updates every week across production, sales, procurement, dispatch, finance, and support teams. Critical business knowledge often stays buried inside chats, emails, and status updates, making it hard for owners to track issues, understand operational health, and make informed decisions.

PulseIQ converts unstructured employee updates into structured business events, builds evidence-backed timelines, and lets owners ask natural-language questions with source-grounded answers and confidence scores.

Instead of acting as a generic chatbot, PulseIQ serves as an operational memory layer for the business: preserving observations, constructing business facts, and generating insights grounded in evidence.

## Key Capabilities

- Multi-tenant architecture for multiple businesses
- Role-based access for super admins, facility admins, and employees
- Natural-language employee updates
- AI-powered event and entity extraction
- Raw entity mention preservation
- Immutable business event store
- Timeline generation
- Hybrid retrieval with SQL and semantic search
- Source-backed answers with confidence scores
- Auditability and trust-first design
- Operational intelligence for manufacturers, traders, distributors, and facility teams

## Example Questions

- What is pending this week?
- Any issues with Rajan Traders?
- How was Line 2 this week?
- Which orders were delayed?
- Which payments are still outstanding?
- Which customers have active issues?
- What operational risks should I be aware of?
- How was this week?

## Core Design Principle

```text
Messages are truth.
Entity mentions are observations.
Canonical entities are interpretations.
Answers are generated from evidence.
```

PulseIQ intentionally preserves raw observations during ingestion. It does not merge `Machine 2` into `Machine 1`, rewrite message facts, or create risky canonical joins while saving employee updates. Query-time retrieval handles exact mentions, aliases, statuses, active issues, broad weekly summaries, and vector search.

## Repository Structure

```text
pulseiq/
|-- pulseiq_backend/    # FastAPI, PostgreSQL, pgvector, Ollama, retrieval, event extraction
`-- pulseiq_frontend/   # Vite, React, TypeScript, Tailwind, role-aware app UI
```

## Product Flow

```text
Employee message
-> Entity/event extraction
-> Raw entity mention storage
-> Business event storage
-> Owner query
-> Entity/status/time-range retrieval
-> Evidence-backed answer generation
```

## Roles

PulseIQ uses backend-enforced roles:

- `super_admin`: creates facilities and facility admins.
- `facility_admin`: creates employees and reviews intelligence for their facility.
- `employee`: submits operational updates.

First-time super-admin creation is protected by `SUPER_ADMIN_SETUP_TOKEN`. There is no public signup flow.

## Tech Stack

Backend:

- FastAPI and Uvicorn
- PostgreSQL with `pgvector`
- SQLAlchemy async ORM
- Alembic migrations
- Redis
- Ollama for local LLM generation and embeddings
- JWT auth and RBAC

Frontend:

- Vite
- React 19
- TypeScript
- Tailwind CSS
- React Router
- TanStack Query
- Framer Motion
- lucide-react icons

## Local Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop
- Ollama model available locally, for example `llama3`

## Backend Setup

From the repository root:

```bash
cd pulseiq_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your local values. Keep real secrets out of git.

Start local services:

```bash
docker compose up -d db redis ollama
```

If the Ollama model is not available yet:

```bash
ollama pull llama3
```

Apply migrations:

```bash
PYTHONPATH=.. alembic upgrade head
```

Run the API:

```bash
PYTHONPATH=.. uvicorn pulseiq_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Frontend Setup

In a second terminal:

```bash
cd pulseiq_frontend
npm install
```

Create an optional local env file if your backend URL differs:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Run the frontend:

```bash
npm run dev
```

Frontend URL:

- App: `http://localhost:5173`

## First-Time App Setup

1. Start backend dependencies and API.
2. Start the frontend.
3. Visit the hidden bootstrap route:

```text
http://localhost:5173/crete-superadmin
```

4. Enter the setup token from backend `.env`.
5. Create facilities as `super_admin`.
6. Create facility admins.
7. Log in as a facility admin and create employees with departments.
8. Employees submit operational messages.
9. Facility admins ask operational questions in the intelligence view.

## Important API Endpoints

Auth:

- `POST /auth/bootstrap-super-admin`
- `POST /auth/login`
- `POST /auth/reset-password`

Facilities:

- `GET /tenants`
- `POST /tenants`

Users:

- `GET /users`
- `POST /users/facility-admins`
- `POST /users/employees`
- `PATCH /users/employees/{user_id}`
- `GET /users/employee-departments`

Operations:

- `GET /messages`
- `POST /messages`
- `POST /query`
- `GET /health`

See the detailed frontend contract in:

```text
pulseiq_backend/docs/frontend-api-spec.md
```

## Intelligence Architecture

PulseIQ separates observations from interpretations:

- `messages`: original employee updates.
- `entity_mentions`: raw extracted observations such as `Machine 2` or `Sharma`.
- `events`: structured business facts such as `payment_pending`, `line_down`, or `blocked`.
- `entities`: optional canonical business entities for future knowledge-graph use.
- `entity_aliases`: optional aliases for query-time matching.

During ingestion, PulseIQ stores the message and raw extracted observations. It avoids automatic merges because false merges are more damaging than duplicates.

During retrieval, PulseIQ ranks evidence using:

1. Raw mention matches
2. Canonical entity and alias matches
3. Event/status category matches such as `pending`, `blocked`, `down`
4. Broad time-range summaries such as `activities this week`
5. Vector retrieval
6. LLM answer generation from retrieved evidence

## Useful Commands

Backend:

```bash
cd pulseiq_backend
source venv/bin/activate
docker compose up -d db redis ollama
PYTHONPATH=.. alembic upgrade head
PYTHONPATH=.. uvicorn pulseiq_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd pulseiq_frontend
npm install
npm run dev
npm run lint
npm run build
```

Git:

```bash
git status
git add .
git commit -m "Describe your change"
git push
```

## Testing and Verification

Frontend checks:

```bash
cd pulseiq_frontend
npm run lint
npm run build
```

Backend lightweight syntax checks can be run with Python. Full test execution requires installing `pytest` in the backend virtual environment.

```bash
cd pulseiq_backend
source venv/bin/activate
python -m compileall services repositories models schemas api
```

## Security Notes

- Do not commit `.env`.
- Do not commit real `SUPER_ADMIN_SETUP_TOKEN` values.
- Do not commit local virtual environments, `node_modules`, or build output.
- Keep setup access hidden from the login UI; use `/crete-superadmin` only for controlled first-time bootstrap.

## Current Status

PulseIQ supports:

- Secure super-admin bootstrap
- Role-aware login and routing
- Facility and user management
- Employee department dropdowns
- Employee update submission
- Background event extraction with Ollama
- Raw entity mention preservation
- Query-time retrieval for entity, status, active issue, and broad weekly summary questions
- Evidence-backed answers with sources, timeline, and confidence
