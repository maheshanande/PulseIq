import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { canAccess, hasAccessToken, mustResetPassword } from "@/lib/api";
import type { UserRole } from "@/lib/types";

export function ProtectedRoute({ children, roles }: { children: ReactNode; roles?: UserRole[] }) {
  const location = useLocation();

  if (!hasAccessToken()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (mustResetPassword() && location.pathname !== "/reset-password") {
    return <Navigate to="/reset-password" replace />;
  }

  if (roles && !canAccess(roles)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
