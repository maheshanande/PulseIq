# PulseIQ Frontend Architecture

PulseIQ is organized around product surfaces rather than low-level file types.

## Folder Structure

```txt
src/
  components/
    domain/        Business UI such as IntelligenceCard, TimelineEvent, HealthScoreCard
    layout/        App shell, sidebar, top navigation
    ui/            Shadcn-style primitives
  features/
    intelligence/  Owner intelligence workspace
    messages/      Employee update archive and filters
    overview/      Home dashboard and update composer
    settings/      Workspace and API configuration
    timeline/      Chronological business events
  lib/
    api.ts         API client and mock fallback
    mock-data.ts   Local demo data
    types.ts       Shared product contracts
    utils.ts       Styling helpers
```

## Design System

- Dark mode first with restrained contrast and muted business tones.
- Cards are used for metrics, intelligence output, repeated records, and framed tools.
- Typography favors compact hierarchy and high information density.
- Motion is limited to card/timeline entrance and does not alter core layout.

## API Integration Guide

Set the API origin:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Expected endpoints:

```txt
GET  /health
POST /auth/login
POST /auth/reset-password
GET  /messages
POST /messages
POST /query
GET  /tenants
POST /tenants
GET  /users
POST /users
```

`POST /auth/login` uses form data:

```txt
username=admin@example.com&password=secret
```

The frontend stores `access_token` in local storage and sends:

```http
Authorization: Bearer <access_token>
```

`POST /messages` request:

```json
{
  "content": "Customer ACME reported that integration testing is blocked by missing API credentials."
}
```

`POST /query` request:

```json
{
  "question": "What is blocking ACME right now?"
}
```

The query response should match `QueryResponse` in `src/lib/types.ts`. The UI renders structured sections and never displays raw JSON.
