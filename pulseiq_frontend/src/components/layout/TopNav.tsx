import { LogOut, UserRound } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { clearSession, getCurrentRole } from "@/lib/api";

export function TopNav() {
  const navigate = useNavigate();
  const role = getCurrentRole();
  const [isAccountOpen, setIsAccountOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/86 backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-[1500px] items-center gap-3 px-4 sm:px-6 lg:px-8">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-foreground">{workspaceTitle(role)}</div>
          <div className="mt-0.5 text-xs text-muted-foreground">{workspaceDescription(role)}</div>
        </div>
        <div className="relative">
          <button
            className="flex h-9 items-center gap-2 rounded-md border border-border bg-card px-2.5 text-sm transition-colors hover:bg-secondary"
            onClick={() => setIsAccountOpen((current) => !current)}
            aria-expanded={isAccountOpen}
            aria-haspopup="menu"
          >
            <span className="hidden text-muted-foreground sm:inline">{role.replace("_", " ")}</span>
            <span className="flex h-6 w-6 items-center justify-center rounded bg-secondary text-xs font-semibold">{role[0].toUpperCase()}</span>
          </button>
          {isAccountOpen ? (
            <div className="absolute right-0 top-11 w-56 overflow-hidden rounded-lg border border-border bg-card shadow-business-card" role="menu">
              <div className="border-b border-border p-3">
                <div className="text-sm font-medium text-foreground">Account</div>
                <div className="mt-1 text-xs capitalize text-muted-foreground">{role.replace("_", " ")}</div>
              </div>
              <button
                className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                onClick={() => {
                  setIsAccountOpen(false);
                  navigate("/settings");
                }}
                role="menuitem"
              >
                <UserRound className="h-4 w-4" />
                View profile
              </button>
              <button
                className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm text-red-200 transition-colors hover:bg-red-400/10"
                onClick={() => {
                  clearSession();
                  navigate("/login", { replace: true });
                }}
                role="menuitem"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}

function workspaceTitle(role: string) {
  if (role === "super_admin") return "PulseIQ Platform";
  if (role === "facility_admin") return "Facility Workspace";
  return "Update Workspace";
}

function workspaceDescription(role: string) {
  if (role === "super_admin") return "Manage facilities and facility admins";
  if (role === "facility_admin") return "Review intelligence and manage employees";
  return "Submit operational updates";
}
