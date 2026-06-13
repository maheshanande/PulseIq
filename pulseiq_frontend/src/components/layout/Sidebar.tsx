import { useQuery } from "@tanstack/react-query";
import { NavLink } from "react-router-dom";
import { Brain, Building2, Clock3, MessageSquareText, Settings, Sparkles, SquarePen, UsersRound, type LucideIcon } from "lucide-react";
import { getCurrentRole, pulseIqApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/lib/types";

type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  roles: UserRole[];
};

const navItems: NavItem[] = [
  { label: "Update", href: "/", icon: SquarePen, roles: ["employee", "facility_admin"] },
  { label: "Intelligence", href: "/intelligence", icon: Brain, roles: ["facility_admin"] },
  { label: "Timeline", href: "/timeline", icon: Clock3, roles: ["facility_admin"] },
  { label: "Messages", href: "/messages", icon: MessageSquareText, roles: ["facility_admin"] },
  { label: "Employees", href: "/settings", icon: UsersRound, roles: ["facility_admin"] },
  { label: "Facilities", href: "/settings", icon: Building2, roles: ["super_admin"] },
  { label: "Settings", href: "/settings", icon: Settings, roles: ["employee"] },
];

export function Sidebar() {
  const role = getCurrentRole();
  const visibleItems = navItems.filter((item) => item.roles.includes(role));
  const health = useQuery({
    queryKey: ["health"],
    queryFn: pulseIqApi.health,
    refetchInterval: 60_000,
    retry: 1,
  });
  const isHealthy = health.data?.status === "ok";

  return (
    <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-border lg:bg-background/94 lg:backdrop-blur">
      <div className="flex h-16 items-center gap-3 px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-md border border-primary/20 bg-primary/10 text-primary">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <div className="text-sm font-bold tracking-normal">PulseIQ</div>
          <div className="text-xs text-muted-foreground">Business OS</div>
        </div>
      </div>
      <nav className="space-y-1 px-3 py-4">
        {visibleItems.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            end={item.href === "/"}
            className={({ isActive }) =>
              cn(
                "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors",
                "hover:bg-secondary hover:text-foreground",
                isActive && "bg-secondary text-foreground",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto border-t border-border p-4">
        <div className="mb-3 rounded-lg border border-border bg-card p-3">
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs font-medium text-foreground">Backend</span>
            <span className={cn("flex items-center gap-1.5 text-xs", isHealthy ? "text-emerald-200" : health.isError ? "text-red-200" : "text-muted-foreground")}>
              <span className={cn("h-1.5 w-1.5 rounded-full", isHealthy ? "bg-emerald-300" : health.isError ? "bg-red-300" : "bg-muted-foreground")} />
              {isHealthy ? "Online" : health.isError ? "Offline" : "Checking"}
            </span>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <div className="text-xs font-medium text-foreground">{roleLabel(role)}</div>
          <div className="mt-1 text-xs leading-5 text-muted-foreground">{roleDescription(role)}</div>
        </div>
      </div>
    </aside>
  );
}

function roleLabel(role: UserRole) {
  if (role === "super_admin") return "Platform Admin";
  if (role === "facility_admin") return "Facility Admin";
  return "Employee";
}

function roleDescription(role: UserRole) {
  if (role === "super_admin") return "Create and manage facilities.";
  if (role === "facility_admin") return "Review intelligence and manage employees.";
  return "Submit operational updates quickly.";
}
