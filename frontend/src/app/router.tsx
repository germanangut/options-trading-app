import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { AppShell } from "./layout/AppShell";
import { AlertsPage } from "../pages/AlertsPage";
import { DailySummaryPage } from "../pages/DailySummaryPage";
import { HistoryPage } from "../pages/HistoryPage";
import { OverviewPage } from "../pages/OverviewPage";
import { PortfolioPage } from "../pages/PortfolioPage";
import { QualifiedTradesPage } from "../pages/QualifiedTradesPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <OverviewPage /> },
      { path: "qualified", element: <QualifiedTradesPage /> },
      { path: "alerts", element: <AlertsPage /> },
      { path: "portfolio", element: <PortfolioPage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "daily-summary", element: <DailySummaryPage /> },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
