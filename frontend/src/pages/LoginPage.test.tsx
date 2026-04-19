import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LoginPage } from "./LoginPage";

vi.mock("../features/auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

const { useAuth } = await import("../features/auth/AuthContext");

afterEach(() => {
  cleanup();
});

function buildAuthContext() {
  return {
    status: "unauthenticated" as const,
    currentUser: null,
    login: vi.fn().mockResolvedValue(undefined),
    register: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    isAuthenticated: false,
  };
}

describe("LoginPage", () => {
  it("renders with the premium dark auth theme classes applied to the main surfaces and controls", () => {
    vi.mocked(useAuth).mockReturnValue(buildAuthContext() as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("login-page-root")).toHaveClass("bg-surface-0", "text-ink-1");
    expect(screen.getByTestId("login-hero-panel")).toHaveClass("panel-shell", "panel-glow");
    expect(screen.getByTestId("login-form")).toBeInTheDocument();
    expect(screen.getByTestId("login-email-input")).toHaveClass("bg-surface-overlay/70", "border-white/10", "text-ink-1");
    expect(screen.getByTestId("login-password-input")).toHaveClass("bg-surface-overlay/70", "border-white/10", "text-ink-1");
    expect(screen.getByTestId("login-submit-button")).toHaveClass("bg-accent", "text-surface-0");
    expect(screen.getByTestId("login-mode-button")).toHaveClass("bg-accent", "text-surface-0");
    expect(screen.getByTestId("register-mode-button")).toHaveClass("bg-surface-2", "text-ink-2");
  });

  it("switches visual state cleanly between login and register modes", () => {
    vi.mocked(useAuth).mockReturnValue(buildAuthContext() as ReturnType<typeof useAuth>);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByTestId("register-mode-button"));

    expect(screen.getAllByText("Create Account").length).toBeGreaterThan(0);
    expect(screen.getByTestId("register-mode-button")).toHaveClass("bg-accent", "text-surface-0");
    expect(screen.getByTestId("login-mode-button")).toHaveClass("bg-surface-2", "text-ink-2");
    expect(screen.getByTestId("login-password-input")).toHaveAttribute("autocomplete", "new-password");
  });
});