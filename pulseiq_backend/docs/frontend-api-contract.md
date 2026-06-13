# PulseIQ Frontend API Contract

Backend app: FastAPI `PulseIQ` v0.1.0

Default local base URL:

```ts
const API_BASE_URL = "http://localhost:8000";
```

All JSON endpoints use:

```http
Content-Type: application/json
```

Authenticated endpoints require:

```http
Authorization: Bearer <access_token>
```

Dates are ISO datetime strings. UUIDs are strings.

## Auth Flow

1. Login with `POST /auth/login`.
2. Store `access_token`.
3. If `must_reset_password` is `true`, force the user to call `POST /auth/reset-password`.
4. Use the bearer token for all protected endpoints.

Token lifetime is 8 hours.

Roles:

```ts
type UserRole = "super_admin" | "facility_admin" | "employee";
type EmployeeDepartment =
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
```

## Shared Types

```ts
export type UUID = string;
export type ISODateTime = string;

export interface ApiError {
  detail: string | Array<Record<string, unknown>>;
}

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

export interface EmployeeDepartmentOption {
  value: EmployeeDepartment;
  label: string;
}

export interface Message {
  id: UUID;
  tenant_id: UUID;
  user_id: UUID | null;
  content: string;
  created_at: ISODateTime;
}

export interface ConfidenceScore {
  score: number;
  label: "High" | "Medium" | "Low" | string;
}

export interface TimelineEntry {
  time: string;
  event: string;
  entity_name: string;
  reported_by: string;
  source_message_ids: UUID[];
}

export interface SourceEntry {
  message_id: UUID;
  submitted_by: string;
  content: string;
}

export interface ReasoningBlock {
  messages_analyzed: number;
  events_found: number;
  entity: string | null;
}

export interface QueryResponse {
  executive_summary: string;
  current_status: string | null;
  assessment: string | null;
  confidence: ConfidenceScore;
  timeline: TimelineEntry[];
  sources: SourceEntry[];
  reasoning: ReasoningBlock;
}
```

## Endpoints

### Health

#### `GET /health`

Auth: none

Response `200`:

```ts
interface HealthResponse {
  status: "ok";
}
```

### Auth

#### `POST /auth/login`

Auth: none

Important: this endpoint expects form data, not JSON.

Request:

```ts
const body = new URLSearchParams({
  username: email,
  password,
});
```

Headers:

```http
Content-Type: application/x-www-form-urlencoded
```

Response `200`:

```ts
interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  must_reset_password: boolean;
}
```

Errors:

```http
401 Invalid credentials
```

#### `POST /auth/reset-password`

Auth: any active logged-in user

Request:

```ts
interface ResetPasswordRequest {
  current_password: string;
  new_password: string;
}
```

Response `200`:

```ts
interface MessageOnlyResponse {
  message: string;
}
```

Errors:

```http
400 Current password is incorrect
400 New password must differ from current
401 Invalid or expired token
```

### Tenants

Only `super_admin` can use these endpoints.

#### `POST /tenants`

Auth: `super_admin`

Request:

```ts
interface TenantCreateRequest {
  name: string;
  slug: string;
}
```

Response `201`: `Tenant`

Errors:

```http
401 Invalid or expired token
403 Insufficient permissions
```

#### `GET /tenants`

Auth: `super_admin`

Response `200`: `Tenant[]`

### Users

User creation is hierarchical: `super_admin` creates facility admins, and `facility_admin` creates employees.

#### `POST /users/facility-admins`

Creates a facility admin for a facility and returns a temporary password.

Auth: `super_admin`

Request:

```ts
interface FacilityAdminCreateRequest {
  tenant_id: UUID;
  email: string;
}
```

Response `201`:

```ts
interface FacilityAdminCreatedResponse {
  user: User;
  temporary_password: string;
  message: string;
}
```

Errors:

```http
401 Invalid or expired token
403 Insufficient permissions
404 Facility not found
409 Email already registered
422 Validation error
```

#### `POST /users/employees`

Creates an employee in the current facility and returns a temporary password.

Auth: `facility_admin`

Request:

```ts
interface EmployeeCreateRequest {
  email: string;
  department: EmployeeDepartment;
}
```

Response `201`:

```ts
interface EmployeeCreatedResponse {
  user: User;
  temporary_password: string;
  message: string;
}
```

Errors:

```http
401 Invalid or expired token
403 Insufficient permissions
409 Email already registered
422 Validation error
```

Legacy alias: `POST /users` behaves the same as `POST /users/employees`.

#### `GET /users/employee-departments`

Returns the standard dropdown options for employee departments.

Auth: `super_admin` or `facility_admin`

Response `200`: `EmployeeDepartmentOption[]`

```ts
[
  { value: "operations", label: "Operations" },
  { value: "sales", label: "Sales" },
  { value: "engineering", label: "Engineering" },
  { value: "customer_support", label: "Customer Support" },
  { value: "customer_success", label: "Customer Success" },
  { value: "product", label: "Product" },
  { value: "marketing", label: "Marketing" },
  { value: "finance", label: "Finance" },
  { value: "human_resources", label: "Human Resources" },
  { value: "administration", label: "Administration" },
  { value: "procurement", label: "Procurement" },
  { value: "logistics", label: "Logistics" },
  { value: "production", label: "Production" },
  { value: "quality_assurance", label: "Quality Assurance" },
  { value: "security", label: "Security" },
  { value: "legal", label: "Legal" },
  { value: "other", label: "Other" }
]
```

#### `GET /users`

Lists users in the current facility.

Auth: `facility_admin`

Response `200`: `User[]`

#### `PATCH /users/employees/{user_id}`

Updates the department for an existing employee in the current facility.

Auth: `facility_admin`

Request:

```ts
interface EmployeeUpdateRequest {
  department: EmployeeDepartment;
}
```

Response `200`: `User`

Errors:

```http
401 Invalid or expired token
403 Insufficient permissions
404 Employee not found
422 Validation error
```

### Messages

#### `POST /messages`

Creates a message for the current user's tenant. The backend starts event extraction in the background after creation.

Auth: any active logged-in user whose `must_reset_password` is `false`

Request:

```ts
interface MessageCreateRequest {
  content: string;
}
```

Response `201`: `Message`

Errors:

```http
401 Invalid or expired token
403 You must reset your password before submitting messages
422 Validation error
```

#### `GET /messages`

Lists recent messages for the current user's tenant.

Auth: any active logged-in user

Response `200`: `Message[]`

### Query

#### `POST /query`

Asks a question against the current tenant's ingested messages and extracted events.

Auth: any active logged-in user

Request:

```ts
interface QueryRequest {
  question: string;
}
```

Response `200`: `QueryResponse`

Errors:

```http
401 Invalid or expired token
422 Validation error
```

## Minimal Fetch Client

```ts
export class PulseIqApi {
  constructor(
    private readonly baseUrl: string,
    private accessToken?: string,
  ) {}

  setToken(token: string | undefined) {
    this.accessToken = token;
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (!(init.body instanceof URLSearchParams)) {
      headers.set("Content-Type", "application/json");
    }
    if (this.accessToken) {
      headers.set("Authorization", `Bearer ${this.accessToken}`);
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw error;
    }

    return response.json() as Promise<T>;
  }

  login(email: string, password: string) {
    return this.request<LoginResponse>("/auth/login", {
      method: "POST",
      body: new URLSearchParams({ username: email, password }),
    });
  }

  resetPassword(body: ResetPasswordRequest) {
    return this.request<MessageOnlyResponse>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  createTenant(body: TenantCreateRequest) {
    return this.request<Tenant>("/tenants", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listTenants() {
    return this.request<Tenant[]>("/tenants");
  }

  createFacilityAdmin(body: FacilityAdminCreateRequest) {
    return this.request<FacilityAdminCreatedResponse>("/users/facility-admins", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  createEmployee(body: EmployeeCreateRequest) {
    return this.request<EmployeeCreatedResponse>("/users/employees", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listEmployeeDepartments() {
    return this.request<EmployeeDepartmentOption[]>("/users/employee-departments");
  }

  listUsers() {
    return this.request<User[]>("/users");
  }

  updateEmployee(userId: UUID, body: EmployeeUpdateRequest) {
    return this.request<User>(`/users/employees/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  createMessage(body: MessageCreateRequest) {
    return this.request<Message>("/messages", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  listMessages() {
    return this.request<Message[]>("/messages");
  }

  askQuestion(body: QueryRequest) {
    return this.request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }
}
```

## Frontend Screens Suggested By Current Backend

- Login
- Forced reset password
- Super admin tenant management
- Facility admin employee management
- Message submission and message feed
- Query/search screen with answer, confidence, timeline, sources, and reasoning

## Backend Integration Notes

- The backend configures CORS from `CORS_ORIGINS` in `.env`.
- `POST /auth/login` uses OAuth2 form encoding. Do not send JSON to that endpoint.
- `POST /messages` triggers async extraction, so query results may lag briefly after a new message is submitted.
- There is no `GET /me` endpoint yet. The frontend can infer `must_reset_password` from login, but it cannot fetch the current user profile directly.
