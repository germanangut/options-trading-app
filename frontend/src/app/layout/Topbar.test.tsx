import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NAV_ITEMS } from "../../lib/constants";
import { Topbar } from "./Topbar";

vi.mock("../../features/auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const { useAuth } = await import("../../features/auth/AuthContext");

afterEach(() => {
  cleanup();
});

function buildAuthContext() {
  return {
    status: "authenticated" as const,
    currentUser: {
      user_id: "user_1",
      email: "trader@example.com",
      auth_provider: "password",
      created_at: "2026-04-19T00:00:00Z",
      last_login_at: "2026-04-19T12:00:00Z",
    },
    login: vi.fn().mockResolvedValue(undefined),
    register: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    isAuthenticated: true,
  };
}

function TopbarHarness({ diagnosticsStatus, onToggleDiagnostics }: {
  diagnosticsStatus?: {
    tone: "success" | "info" | "warning";
    label: string;
    detail: string;
    triggerLabel: string;
  };
  onToggleDiagnostics?: () => void;
}) {
  const location = useLocation();

  return <Topbar pathname={location.pathname} diagnosticsStatus={diagnosticsStatus ?? null} onToggleDiagnostics={onToggleDiagnostics} />;
}

function renderTopbar(initialEntry = "/", diagnosticsStatus?: {
  tone: "success" | "info" | "warning";
  label: string;
  detail: string;
  triggerLabel: string;
}) {
  vi.mocked(useAuth).mockReturnValue(buildAuthContext() as ReturnType<typeof useAuth>);
  const onToggleDiagnostics = vi.fn();

  const rendered = render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>Overview Screen</div></>} />
        <Route path="/qualified" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>Qualified Trades Screen</div></>} />
        <Route path="/alerts" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>Alerts Screen</div></>} />
        <Route path="/history" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>History Screen</div></>} />
        <Route path="/daily-summary" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>Daily Summary Screen</div></>} />
        <Route path="/portfolio" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>Portfolio Screen</div></>} />
        <Route path="/paper-dashboard" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>Paper Dashboard Screen</div></>} />
        <Route path="/scans/:scanId/trades/:tradeId" element={<><TopbarHarness diagnosticsStatus={diagnosticsStatus} onToggleDiagnostics={onToggleDiagnostics} /><div>Trade Detail Screen</div></>} />
      </Routes>
    </MemoryRouter>,
  );

  return {
    ...rendered,
    onToggleDiagnostics,
  };
}

describe("Topbar", () => {
  it("renders the compact workspace navigation with links to every core page", () => {
    renderTopbar();

    expect(screen.getByTestId("workspace-nav")).toBeInTheDocument();
    NAV_ITEMS.forEach((item) => {
      expect(screen.getByRole("link", { name: item.label })).toBeInTheDocument();
    });
  });

  it("highlights the active route and keeps the qualified tab active on trade detail routes", () => {
    renderTopbar("/history");

    expect(screen.getByRole("link", { name: "History" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Overview" })).not.toHaveAttribute("aria-current");

    cleanup();
    renderTopbar("/scans/scan_1/trades/trade_1");

    expect(screen.getByRole("link", { name: "Qualified Trades" })).toHaveAttribute("aria-current", "page");
  });

  it("navigates across all core pages from the workspace navigation", () => {
    renderTopbar();

    const destinations = [
      { label: "Overview", content: "Overview Screen" },
      { label: "Qualified Trades", content: "Qualified Trades Screen" },
      { label: "Alerts", content: "Alerts Screen" },
      { label: "History", content: "History Screen" },
      { label: "Daily Summary", content: "Daily Summary Screen" },
      { label: "Portfolio", content: "Portfolio Screen" },
      { label: "Paper Dashboard", content: "Paper Dashboard Screen" },
    ];

    destinations.forEach((destination) => {
      fireEvent.click(screen.getByRole("link", { name: destination.label }));
      expect(screen.getByText(destination.content)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: destination.label })).toHaveAttribute("aria-current", "page");
    });
  });

  it("renders the compact diagnostics status and opens the diagnostics trigger", () => {
    const { onToggleDiagnostics } = renderTopbar("/", {
      tone: "warning",
      label: "Provider slower than usual",
      detail: "The latest run completed, but provider timing exceeded the normal range.",
      triggerLabel: "View diagnostics",
    });

    expect(screen.getByTestId("diagnostics-status")).toBeInTheDocument();
    expect(screen.getByText("Provider slower than usual")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));
    expect(onToggleDiagnostics).toHaveBeenCalledTimes(1);
  });
});