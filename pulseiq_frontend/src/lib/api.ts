import type {
  CreateUserResponse,
  EmployeeDepartment,
  EmployeeDepartmentOption,
  LoginResponse,
  Message,
  QueryResponse,
  Tenant,
  User,
  UserRole,
} from "@/lib/types";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_KEY = "pulseiq_access_token";
const RESET_KEY = "pulseiq_must_reset_password";
const SESSION_MESSAGE_KEY = "pulseiq_session_message";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function hasAccessToken() {
  return Boolean(getAccessToken());
}

export function mustResetPassword() {
  return localStorage.getItem(RESET_KEY) === "true";
}

export function saveSession(response: LoginResponse) {
  localStorage.setItem(TOKEN_KEY, response.access_token);
  localStorage.setItem(RESET_KEY, String(response.must_reset_password));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(RESET_KEY);
}

export function consumeSessionMessage() {
  const message = sessionStorage.getItem(SESSION_MESSAGE_KEY);
  if (message) {
    sessionStorage.removeItem(SESSION_MESSAGE_KEY);
  }
  return message;
}

export function getCurrentRole(): UserRole {
  const token = getAccessToken();
  if (!token) return "employee";

  try {
    const encodedPayload = token.split(".")[1] ?? "";
    const normalizedPayload = encodedPayload.replace(/-/g, "+").replace(/_/g, "/");
    const payload = JSON.parse(atob(normalizedPayload.padEnd(Math.ceil(normalizedPayload.length / 4) * 4, "=")));
    const role = payload.role ?? payload.user_role ?? payload.user?.role;
    if (role === "super_admin" || role === "facility_admin" || role === "employee") {
      return role;
    }
    return "employee";
  } catch {
    return "employee";
  }
}

export function canAccess(requiredRoles: UserRole[]) {
  return requiredRoles.includes(getCurrentRole());
}

function authHeaders(attachAuth = true) {
  if (!attachAuth) return {};
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function isTokenFailure(status: number, message: string) {
  const normalized = message.toLowerCase();
  return (
    status === 401 ||
    normalized.includes("invalid token") ||
    normalized.includes("expired token") ||
    normalized.includes("token expired") ||
    normalized.includes("could not validate credentials")
  );
}

function forceLogout(message = "Your session expired. Please sign in again.") {
  clearSession();
  sessionStorage.setItem(SESSION_MESSAGE_KEY, message);
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const attachAuth = path !== "/auth/login" && path !== "/auth/bootstrap-super-admin";
  const hadToken = attachAuth && hasAccessToken();
  const isFormData = init.body instanceof URLSearchParams;
  const headers = new Headers(init.headers);
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  Object.entries(authHeaders(attachAuth)).forEach(([key, value]) => {
    headers.set(key, value);
  });

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let message = `PulseIQ API error ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (Array.isArray(payload.detail)) {
        message = payload.detail.map((error: { msg: string }) => error.msg).join(", ");
      }
    } catch {
      // Keep the HTTP status fallback if the response is not JSON.
    }
    if (hadToken && isTokenFailure(response.status, message)) {
      forceLogout();
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export const pulseIqApi = {
  health() {
    return request<{ status: "ok" | string }>("/health");
  },

  login(username: string, password: string) {
    const body = new URLSearchParams();
    body.set("username", username);
    body.set("password", password);
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },

  bootstrapSuperAdmin(email: string, password: string, setup_token: string) {
    return request<LoginResponse>("/auth/bootstrap-super-admin", {
      method: "POST",
      body: JSON.stringify({ email, password, setup_token }),
    });
  },

  resetPassword(current_password: string, new_password: string) {
    return request<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password }),
    });
  },

  getMessages() {
    return request<Message[]>("/messages");
  },

  createMessage(content: string) {
    return request<Message>("/messages", {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  query(question: string) {
    return request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    });
  },

  getTenants() {
    return request<Tenant[]>("/tenants");
  },

  createTenant(name: string, slug: string) {
    return request<Tenant>("/tenants", {
      method: "POST",
      body: JSON.stringify({ name, slug }),
    });
  },

  getUsers() {
    return request<User[]>("/users");
  },

  getEmployeeDepartments() {
    return request<EmployeeDepartmentOption[]>("/users/employee-departments");
  },

  createFacilityAdmin(tenant_id: string, email: string) {
    return request<CreateUserResponse>("/users/facility-admins", {
      method: "POST",
      body: JSON.stringify({ tenant_id, email }),
    });
  },

  createEmployee(email: string, department: EmployeeDepartment) {
    return request<CreateUserResponse>("/users/employees", {
      method: "POST",
      body: JSON.stringify({ email, department }),
    });
  },

  updateEmployeeDepartment(userId: string, department: EmployeeDepartment) {
    return request<User>(`/users/employees/${userId}`, {
      method: "PATCH",
      body: JSON.stringify({ department }),
    });
  },
};
