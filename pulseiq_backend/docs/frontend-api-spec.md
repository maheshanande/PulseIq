# PulseIQ API Spec For Frontend

Base URL for local development:

```text
http://localhost:8000
```

Authentication:

```http
Authorization: Bearer <access_token>
```

All endpoints use JSON request/response bodies except `POST /auth/login`, which uses form data.

Common error shape:

```json
{
  "detail": "Error message"
}
```

Validation errors may return:

```json
{
  "detail": [
    {
      "type": "string",
      "loc": ["body", "field_name"],
      "msg": "string",
      "input": "value"
    }
  ]
}
```

## 1. Health

### GET `/health`

Auth required: No

Request body: None

Success `200`

```json
{
  "status": "ok"
}
```

## 2. Auth

### POST `/auth/bootstrap-super-admin`

Creates the first `super_admin` account and returns a login token.

Auth required: No

Security:

- Requires `setup_token` to match backend `SUPER_ADMIN_SETUP_TOKEN`.
- Only works while no `super_admin` user exists.
- Password must be at least 12 characters.

Request body:

```json
{
  "email": "super.admin@example.com",
  "password": "long-secure-password",
  "setup_token": "backend-setup-token"
}
```

Success `201`

```json
{
  "access_token": "jwt-token-string",
  "token_type": "bearer",
  "must_reset_password": false
}
```

Errors:

| Status | Meaning |
|---:|---|
| `403` | Invalid setup token |
| `409` | Super admin already exists or email already registered |
| `422` | Invalid request body or password too short |
| `503` | Super admin bootstrap is not configured |

### POST `/auth/login`

Auth required: No

Content-Type:

```http
application/x-www-form-urlencoded
```

Request form fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `username` | string | Yes | User email |
| `password` | string | Yes | User password |

Example request:

```text
username=admin@example.com&password=secret
```

Success `200`

```json
{
  "access_token": "jwt-token-string",
  "token_type": "bearer",
  "must_reset_password": false
}
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid credentials |
| `422` | Invalid form data |

Frontend behavior:

- Store `access_token`.
- Send it as `Authorization: Bearer <access_token>` for protected APIs.
- If `must_reset_password` is `true`, route user to reset password before allowing message submission.

### POST `/auth/reset-password`

Auth required: Yes

Request body:

```json
{
  "current_password": "old-password",
  "new_password": "new-password"
}
```

Success `200`

```json
{
  "message": "Password updated successfully"
}
```

Errors:

| Status | Meaning |
|---:|---|
| `400` | Current password is incorrect |
| `400` | New password must differ from current |
| `401` | Invalid or expired token |
| `422` | Invalid request body |

## 3. Tenants

These APIs are for `super_admin` users only.

### POST `/tenants`

Auth required: Yes, `super_admin`

Request body:

```json
{
  "name": "Acme Corp",
  "slug": "acme"
}
```

Success `201`

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "name": "Acme Corp",
  "slug": "acme",
  "created_at": "2026-06-13T10:30:00Z"
}
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | Insufficient permissions |
| `409` | Facility name or slug already exists |
| `422` | Invalid request body |

### GET `/tenants`

Auth required: Yes, `super_admin`

Request body: None

Success `200`

```json
[
  {
    "id": "00000000-0000-0000-0000-000000000000",
    "name": "Acme Corp",
    "slug": "acme",
    "created_at": "2026-06-13T10:30:00Z"
  }
]
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | Insufficient permissions |

## 4. Users

User creation is hierarchical:

- `super_admin` creates facility admins.
- `facility_admin` creates employees inside their own facility.

Important naming:

- `role` is the backend permission role: `super_admin`, `facility_admin`, or `employee`.
- `department` is the employee's business/job area and should be shown as a dropdown in the frontend.

### POST `/users/facility-admins`

Creates a facility admin for a facility.

Auth required: Yes, `super_admin`

Request body:

```json
{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "email": "facility.admin@example.com"
}
```

Success `201`

```json
{
  "user": {
    "id": "00000000-0000-0000-0000-000000000000",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "email": "facility.admin@example.com",
    "role": "facility_admin",
    "department": null,
    "is_active": true,
    "must_reset_password": true,
    "created_at": "2026-06-13T10:30:00Z"
  },
  "temporary_password": "temporary-password",
  "message": "Share this temporary password with facility admin facility.admin@example.com. They must reset it on first login."
}
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | Insufficient permissions |
| `404` | Facility not found |
| `409` | Email already registered |
| `422` | Invalid request body |

### POST `/users/employees`

Creates an employee under the current facility admin's facility.

Auth required: Yes, `facility_admin`

Request body:
 
```json
{
  "email": "employee@example.com",
  "department": "engineering"
}
```

Success `201`

```json
{
  "user": {
    "id": "00000000-0000-0000-0000-000000000000",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "email": "employee@example.com",
    "role": "employee",
    "department": "engineering",
    "is_active": true,
    "must_reset_password": true,
    "created_at": "2026-06-13T10:30:00Z"
  },
  "temporary_password": "temporary-password",
  "message": "Share this temporary password with employee@example.com. They must reset it on first login."
}
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | Insufficient permissions |
| `409` | Email already registered |
| `422` | Invalid email/request body |

Legacy alias:

```text
POST /users
```

This currently behaves the same as `POST /users/employees` for backward compatibility. New frontend code should use `POST /users/employees`.

### GET `/users/employee-departments`

Returns standard employee department dropdown options.

Auth required: Yes, `super_admin` or `facility_admin`

Request body: None

Success `200`

```json
[
  { "value": "operations", "label": "Operations" },
  { "value": "sales", "label": "Sales" },
  { "value": "engineering", "label": "Engineering" },
  { "value": "customer_support", "label": "Customer Support" },
  { "value": "customer_success", "label": "Customer Success" },
  { "value": "product", "label": "Product" },
  { "value": "marketing", "label": "Marketing" },
  { "value": "finance", "label": "Finance" },
  { "value": "human_resources", "label": "Human Resources" },
  { "value": "administration", "label": "Administration" },
  { "value": "procurement", "label": "Procurement" },
  { "value": "logistics", "label": "Logistics" },
  { "value": "production", "label": "Production" },
  { "value": "quality_assurance", "label": "Quality Assurance" },
  { "value": "security", "label": "Security" },
  { "value": "legal", "label": "Legal" },
  { "value": "other", "label": "Other" }
]
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | Insufficient permissions |

### GET `/users`

Lists users in the current facility admin's facility.

Auth required: Yes, `facility_admin`

Request body: None

Success `200`

```json
[
  {
    "id": "00000000-0000-0000-0000-000000000000",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "email": "employee@example.com",
    "role": "employee",
    "department": "engineering",
    "is_active": true,
    "must_reset_password": false,
    "created_at": "2026-06-13T10:30:00Z"
  }
]
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | Insufficient permissions |

### PATCH `/users/employees/{user_id}`

Updates the department for an existing employee in the current facility admin's facility.

Auth required: Yes, `facility_admin`

Request body:

```json
{
  "department": "operations"
}
```

Success `200`

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "email": "employee@example.com",
  "role": "employee",
  "department": "operations",
  "is_active": true,
  "must_reset_password": false,
  "created_at": "2026-06-13T10:30:00Z"
}
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | Insufficient permissions |
| `404` | Employee not found |
| `422` | Invalid request body |

## 5. Messages

### POST `/messages`

Creates a message for the logged-in user's tenant.

Auth required: Yes

Request body:

```json
{
  "content": "Customer ACME reported that integration testing is blocked by missing API credentials."
}
```

Success `201`

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "user_id": "22222222-2222-2222-2222-222222222222",
  "content": "Customer ACME reported that integration testing is blocked by missing API credentials.",
  "created_at": "2026-06-13T10:30:00Z"
}
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `403` | User must reset password before submitting messages |
| `422` | Invalid request body |

Notes for frontend:

- The backend runs event extraction in the background after message creation.
- Query results may not include the new message immediately.

### GET `/messages`

Lists recent messages for the logged-in user's tenant.

Auth required: Yes

Request body: None

Success `200`

```json
[
  {
    "id": "00000000-0000-0000-0000-000000000000",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "user_id": "22222222-2222-2222-2222-222222222222",
    "content": "Customer ACME reported that integration testing is blocked by missing API credentials.",
    "created_at": "2026-06-13T10:30:00Z"
  }
]
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |

## 6. Query

### POST `/query`

Asks a question against the current tenant's messages and extracted events.

Auth required: Yes

Request body:

```json
{
  "question": "What is blocking ACME right now?"
}
```

Success `200`

```json
{
  "executive_summary": "ACME is currently blocked by missing API credentials required for integration testing.",
  "current_status": "Blocked",
  "assessment": "The issue appears actionable and depends on credentials being shared.",
  "confidence": {
    "score": 0.86,
    "label": "High"
  },
  "timeline": [
    {
      "time": "2026-06-13T10:30:00Z",
      "event": "Integration testing blocked by missing API credentials",
      "entity_name": "ACME",
      "reported_by": "Employee",
      "source_message_ids": [
        "00000000-0000-0000-0000-000000000000"
      ]
    }
  ],
  "sources": [
    {
      "message_id": "00000000-0000-0000-0000-000000000000",
      "submitted_by": "employee",
      "content": "Customer ACME reported that integration testing is blocked by missing API credentials."
    }
  ],
  "reasoning": {
    "messages_analyzed": 10,
    "events_found": 1,
    "entity": "ACME"
  }
}
```

Errors:

| Status | Meaning |
|---:|---|
| `401` | Invalid or expired token |
| `422` | Invalid request body |

## Frontend Type Reference

```ts
export type UUID = string;
export type ISODateTime = string;
export type UserRole = "super_admin" | "facility_admin" | "employee";
export type EmployeeDepartment =
  | "operations"
  | "sales"
  | "engineering"
  | "customer_support"
  | "customer_success"
  | "product"
  | "marketing"
  | "finance"
  | "human_resources"
  | "administration"
  | "procurement"
  | "logistics"
  | "production"
  | "quality_assurance"
  | "security"
  | "legal"
  | "other";

export interface Tenant {
  id: UUID;
  name: string;
  slug: string;
  created_at: ISODateTime;
}

export interface User {
  id: UUID;
  tenant_id: UUID | null;
  email: string;
  role: UserRole;
  department: EmployeeDepartment | null;
  is_active: boolean;
  must_reset_password: boolean;
  created_at: ISODateTime;
}

export interface Message {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID | null;
  content: string;
  created_at: ISODateTime;
}

export interface QueryResponse {
  executive_summary: string;
  current_status: string | null;
  assessment: string | null;
  confidence: {
    score: number;
    label: "High" | "Medium" | "Low" | string;
  };
  timeline: Array<{
    time: string;
    event: string;
    entity_name: string;
    reported_by: string;
    source_message_ids: UUID[];
  }>;
  sources: Array<{
    message_id: UUID;
    submitted_by: string;
    content: string;
  }>;
  reasoning: {
    messages_analyzed: number;
    events_found: number;
    entity: string | null;
  };
}
```
