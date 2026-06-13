import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { ForgotPasswordPage } from "@/features/auth/ForgotPasswordPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { ResetPasswordPage } from "@/features/auth/ResetPasswordPage";
import { SetupSuperAdminPage } from "@/features/auth/SetupSuperAdminPage";
import { OverviewPage } from "@/features/overview/OverviewPage";
import { IntelligencePage } from "@/features/intelligence/IntelligencePage";
import { TimelinePage } from "@/features/timeline/TimelinePage";
import { MessagesPage } from "@/features/messages/MessagesPage";
import { SettingsPage } from "@/features/settings/SettingsPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/crete-superadmin", element: <SetupSuperAdminPage /> },
  { path: "/setup", element: <Navigate to="/login" replace /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <OverviewPage /> },
      {
        path: "intelligence",
        element: (
          <ProtectedRoute roles={["facility_admin"]}>
            <IntelligencePage />
          </ProtectedRoute>
        ),
      },
      {
        path: "timeline",
        element: (
          <ProtectedRoute roles={["facility_admin"]}>
            <TimelinePage />
          </ProtectedRoute>
        ),
      },
      {
        path: "messages",
        element: (
          <ProtectedRoute roles={["facility_admin"]}>
            <MessagesPage />
          </ProtectedRoute>
        ),
      },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
