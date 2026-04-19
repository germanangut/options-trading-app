import { expect, test } from "@playwright/test";

import { openAuthenticatedPage } from "./helpers/visualAppHarness";

test.describe("Dashboard page visual QA", () => {
  test("renders the overview cockpit with the expected hierarchy, colors, and typography", async ({ page }) => {
    await openAuthenticatedPage(page, "/");

    const title = page.getByRole("heading", { name: "Decision cockpit" });
    await expect(title).toBeVisible();
    await expect(title).toHaveCSS("color", "rgb(241, 245, 249)");

    const heroPanel = page.locator("section", { has: title }).first();
    await expect(heroPanel).toHaveClass(/bg-surface-1\/86/);
    await expect(heroPanel).toHaveClass(/shadow-panel/);

    const reviewTradeButton = page.getByRole("link", { name: "Review trade" });
    await expect(reviewTradeButton).toHaveCSS("background-color", "rgb(57, 192, 187)");
    await expect(reviewTradeButton).toHaveCSS("color", "rgb(6, 11, 20)");

    await expect(page.getByRole("heading", { name: "Healthy run with actionable output" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Alert pressure is active" })).toBeVisible();

    await expect(page).toHaveScreenshot("overview-page.png", {
      animations: "disabled",
      fullPage: true,
    });
  });

  test("renders the qualified trades board with stable card styling and emphasis states", async ({ page }) => {
    await openAuthenticatedPage(page, "/qualified");

    const title = page.getByRole("heading", { name: "Ranked decision board" });
    await expect(title).toBeVisible();
    await expect(title).toHaveCSS("color", "rgb(241, 245, 249)");

    const leadIdeaPanel = page.getByText("Lead idea").locator("..");
    await expect(leadIdeaPanel).toHaveClass(/bg-accent-soft\/24/);
    await expect(leadIdeaPanel).toHaveClass(/border-accent\/20/);

    const leadBriefButton = page.getByRole("link", { name: "Open lead brief" });
    await expect(leadBriefButton).toHaveCSS("background-color", "rgb(57, 192, 187)");
    await expect(leadBriefButton).toHaveCSS("color", "rgb(6, 11, 20)");

    await expect(page.getByRole("heading", { name: "AAPL - Bull Put Spread" })).toBeVisible();
    await expect(page.locator("p", { hasText: "Quality ribbon" }).first()).toBeVisible();
    await expect(page.locator("p", { hasText: "Portfolio Impact" }).first()).toBeVisible();

    await expect(page).toHaveScreenshot("qualified-trades-page.png", {
      animations: "disabled",
      fullPage: true,
    });
  });
});