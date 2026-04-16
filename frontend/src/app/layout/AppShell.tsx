import { Outlet, useLocation } from "react-router-dom";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-surface-0 text-ink-1">
      <div className="grid min-h-screen lg:grid-cols-[280px_minmax(0,1fr)]">
        <Sidebar />
        <div className="flex min-h-screen min-w-0 flex-col">
          <Topbar pathname={location.pathname} />
          <main className="flex-1 p-4 sm:p-6 lg:p-8">
            <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
