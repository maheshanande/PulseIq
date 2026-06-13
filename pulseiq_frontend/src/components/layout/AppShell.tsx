import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNav } from "@/components/layout/TopNav";

export function AppShell() {
  return (
    <div className="min-h-screen bg-background">
      <div className="fixed inset-0 -z-10 surface-grid opacity-35" />
      <Sidebar />
      <div className="min-h-screen pl-0 lg:pl-64">
        <TopNav />
        <main className="mx-auto w-full max-w-[1500px] px-4 py-5 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
