import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { getCurrentRole, pulseIqApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { EmployeeDepartment, EmployeeDepartmentOption } from "@/lib/types";

const fallbackEmployeeDepartments: EmployeeDepartmentOption[] = [
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
  { value: "other", label: "Other" },
];

export function SettingsPage() {
  const role = getCurrentRole();

  return (
    <div className="space-y-5">
      <section>
        <h1 className="text-2xl font-semibold tracking-normal">{role === "super_admin" ? "Facilities" : role === "facility_admin" ? "Employees" : "Settings"}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{pageDescription(role)}</p>
      </section>
      {role === "super_admin" ? <SuperAdminFacilities /> : null}
      {role === "facility_admin" ? <FacilityAdminUsers /> : null}
      {role === "employee" ? <EmployeeSettings /> : null}
    </div>
  );
}

function pageDescription(role: string) {
  if (role === "super_admin") return "Create facilities and assign facility admins.";
  if (role === "facility_admin") return "Create employee accounts for your facility.";
  return "Your account and backend connection details.";
}

function EmployeeSettings() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Employee Access</CardTitle>
      </CardHeader>
      <CardContent className="text-sm leading-6 text-muted-foreground">
        Your workspace is focused on submitting operational updates. Facility admins review messages and intelligence.
      </CardContent>
    </Card>
  );
}

function SuperAdminFacilities() {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [facilityAdminEmail, setFacilityAdminEmail] = useState("");
  const [selectedTenantId, setSelectedTenantId] = useState("");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const queryClient = useQueryClient();
  const tenants = useQuery({ queryKey: ["tenants"], queryFn: pulseIqApi.getTenants, retry: false });
  const facilityOptions = tenants.data ?? [];
  const activeTenantId = selectedTenantId || facilityOptions[0]?.id || "";
  const createTenant = useMutation({
    mutationFn: () => pulseIqApi.createTenant(name, slug),
    onSuccess: () => {
      setName("");
      setSlug("");
      void queryClient.invalidateQueries({ queryKey: ["tenants"] });
    },
  });
  const createFacilityAdmin = useMutation({
    mutationFn: () => pulseIqApi.createFacilityAdmin(activeTenantId, facilityAdminEmail),
    onSuccess: (response) => {
      setFacilityAdminEmail("");
      setTemporaryPassword(response.temporary_password);
    },
  });

  function onCreateTenant(event: FormEvent) {
    event.preventDefault();
    if (name && slug) createTenant.mutate();
  }

  function onCreateFacilityAdmin(event: FormEvent) {
    event.preventDefault();
    if (activeTenantId && facilityAdminEmail) createFacilityAdmin.mutate();
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
      <Card>
        <CardHeader>
          <CardTitle>Facilities</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form className="grid gap-3 md:grid-cols-[1fr_1fr_auto]" onSubmit={onCreateTenant}>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Acme Corp" />
            <Input value={slug} onChange={(event) => setSlug(event.target.value)} placeholder="acme" />
            <Button disabled={!name || !slug || createTenant.isPending}>{createTenant.isPending ? "Creating..." : "Create"}</Button>
          </form>
          {createTenant.error ? <p className="text-sm text-red-200">{createTenant.error.message}</p> : null}
          {tenants.error ? <p className="text-sm text-muted-foreground">Facilities require a super_admin token. {tenants.error.message}</p> : null}
          <div className="space-y-2">
            {facilityOptions.map((tenant) => (
              <div key={tenant.id} className="rounded-md border border-border bg-background/45 p-3">
                <div className="text-sm font-medium text-foreground">{tenant.name}</div>
                <div className="text-xs text-muted-foreground">{tenant.slug} · {tenant.id}</div>
              </div>
            ))}
            {!facilityOptions.length && !tenants.isLoading ? <p className="text-sm text-muted-foreground">No facilities yet.</p> : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Facility Admin</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form className="space-y-3" onSubmit={onCreateFacilityAdmin}>
            <Select value={activeTenantId} onChange={(event) => setSelectedTenantId(event.target.value)} disabled={!facilityOptions.length}>
              {facilityOptions.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </option>
              ))}
            </Select>
            <Input value={facilityAdminEmail} onChange={(event) => setFacilityAdminEmail(event.target.value)} type="email" placeholder="facility.admin@example.com" />
            <Button className="w-full" disabled={!activeTenantId || !facilityAdminEmail || createFacilityAdmin.isPending}>
              {createFacilityAdmin.isPending ? "Creating..." : "Create Facility Admin"}
            </Button>
          </form>
          {temporaryPassword ? (
            <div className="rounded-md border border-amber-400/20 bg-amber-400/10 p-3 text-sm text-amber-100">
              Temporary password: <code>{temporaryPassword}</code>
            </div>
          ) : null}
          {createFacilityAdmin.error ? <p className="text-sm text-red-200">{createFacilityAdmin.error.message}</p> : null}
          {!facilityOptions.length && !tenants.isLoading ? <p className="text-sm text-muted-foreground">Create a facility before adding a facility admin.</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}

function FacilityAdminUsers() {
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState<EmployeeDepartment>("operations");
  const [temporaryPassword, setTemporaryPassword] = useState("");
  const queryClient = useQueryClient();
  const users = useQuery({ queryKey: ["users"], queryFn: pulseIqApi.getUsers, retry: false });
  const departments = useQuery({
    queryKey: ["employee-departments"],
    queryFn: pulseIqApi.getEmployeeDepartments,
    retry: false,
  });
  const departmentOptions = departments.data?.length ? departments.data : fallbackEmployeeDepartments;
  const departmentLabels = new Map(departmentOptions.map((option) => [option.value, option.label]));
  const createUser = useMutation({
    mutationFn: () => pulseIqApi.createEmployee(email, department),
    onSuccess: (response) => {
      setEmail("");
      setDepartment(departmentOptions[0]?.value ?? "operations");
      setTemporaryPassword(response.temporary_password);
      void queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
  const updateDepartment = useMutation({
    mutationFn: ({ userId, nextDepartment }: { userId: string; nextDepartment: EmployeeDepartment }) =>
      pulseIqApi.updateEmployeeDepartment(userId, nextDepartment),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (email) createUser.mutate();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Users</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form className="grid gap-3 md:grid-cols-[minmax(0,1fr)_220px_auto]" onSubmit={onSubmit}>
          <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="employee@example.com" />
          <Select
            value={department}
            onChange={(event) => setDepartment(event.target.value as EmployeeDepartment)}
            aria-label="Employee department"
          >
            {departmentOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Button disabled={!email || !department || createUser.isPending}>{createUser.isPending ? "Creating..." : "Create Employee"}</Button>
        </form>
        <p className="text-xs text-muted-foreground">
          Choose the employee's department so PulseIQ can group people by operational function when the backend supports that field.
        </p>
        {temporaryPassword ? (
          <div className="rounded-md border border-amber-400/20 bg-amber-400/10 p-3 text-sm text-amber-100">
            Temporary password: <code>{temporaryPassword}</code>
          </div>
        ) : null}
        {createUser.error ? <p className="text-sm text-red-200">{createUser.error.message}</p> : null}
        {departments.error ? <p className="text-sm text-muted-foreground">Using built-in department options. {departments.error.message}</p> : null}
        {users.error ? <p className="text-sm text-muted-foreground">Users require a facility_admin token. {users.error.message}</p> : null}
        {updateDepartment.error ? <p className="text-sm text-red-200">{updateDepartment.error.message}</p> : null}
        <div className="space-y-2">
          {(users.data ?? []).map((user) => (
            <div key={user.id} className="grid gap-3 rounded-md border border-border bg-background/45 p-3 md:grid-cols-[minmax(0,1fr)_220px] md:items-center">
              <div>
                <div className="text-sm font-medium text-foreground">{user.email}</div>
                <div className="text-xs text-muted-foreground">
                  {user.role}
                  {user.department ? ` · ${departmentLabels.get(user.department) ?? user.department}` : ""}
                  {" · "}
                  {user.must_reset_password ? "must reset password" : "active"}
                </div>
              </div>
              {user.role === "employee" ? (
                <Select
                  value={user.department ?? "other"}
                  onChange={(event) =>
                    updateDepartment.mutate({
                      userId: user.id,
                      nextDepartment: event.target.value as EmployeeDepartment,
                    })
                  }
                  disabled={updateDepartment.isPending}
                  aria-label={`Department for ${user.email}`}
                >
                  {departmentOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              ) : null}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
