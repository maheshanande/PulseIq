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

export interface EmployeeDepartmentOption {
  value: EmployeeDepartment;
  label: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer" | string;
  must_reset_password: boolean;
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

export interface CreateUserResponse {
  user: User;
  temporary_password: string;
  message: string;
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

export interface ApiErrorPayload {
  detail: string | Array<{ type: string; loc: string[]; msg: string; input: unknown }>;
}
