import { Navigate, Outlet, RouterProvider, createBrowserRouter } from "react-router-dom";

import { AppShell } from "./layout/AppShell";
import { useAuth } from "../features/auth/AuthContext";
import { AlertsPage } from "../pages/AlertsPage";
import { DailySummaryPage } from "../pages/DailySummaryPage";
import { HistoryPage } from "../pages/HistoryPage";
import { LoginPage } from "../pages/LoginPage";
import { OverviewPage } from "../pages/OverviewPage";
import { PaperDashboardPage } from "../pages/PaperDashboardPage";
import { PortfolioPage } from "../pages/PortfolioPage";
import { QualifiedTradeDetailPage } from "../pages/QualifiedTradeDetailPage";
import { QualifiedTradesPage } from "../pages/QualifiedTradesPage";


function AuthLoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0 px-4 text-ink-2">
      <div className="rounded-2xl border border-slate-200 bg-white px-6 py-5 text-sm shadow-sm">
        Validating session...
      </div>
    </div>
  );
}


function ProtectedLayout() {
  const auth = useAuth();

  if (auth.status === "loading") {
    return <AuthLoadingScreen />;
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <AppShell />;
}


function PublicAuthLayout() {
  const auth = useAuth();

  if (auth.status === "loading") {
    return <AuthLoadingScreen />;
  }

  if (auth.isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

const router = createBrowserRouter([
  {
    element: <PublicAuthLayout />,
    children: [{ path: "/login", element: <LoginPage /> }],
  },
  {
    path: "/",
    element: <ProtectedLayout />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "qualified", element: <QualifiedTradesPage /> },
      { path: "scans/:scanId/trades/:tradeId", element: <QualifiedTradeDetailPage /> },
      { path: "alerts", element: <AlertsPage /> },
      { path: "portfolio", element: <PortfolioPage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "daily-summary", element: <DailySummaryPage /> },
      { path: "paper-dashboard", element: <PaperDashboardPage /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
