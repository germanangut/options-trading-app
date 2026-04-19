import { expect, test } from "@playwright/test";

test.describe("Login page visual QA", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.clear();
      window.sessionStorage.clear();
    });

    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/login");
    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation: none !important;
          transition: none !important;
          caret-color: transparent !important;
        }
      `,
    });
  });

  test("renders the login mode with the expected colors, typography, and layout", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "App Identity First" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Sign In" })).toBeVisible();

    const theme = await page.locator("[data-testid='login-page-root']").evaluate((element) => {
      const styles = window.getComputedStyle(element);
      const bodyStyles = window.getComputedStyle(document.body);
      return {
        backgroundColor: styles.backgroundColor,
        textColor: styles.color,
        fontFamily: bodyStyles.fontFamily,
      };
    });

    expect(theme.backgroundColor).toBe("rgb(6, 11, 20)");
    expect(theme.textColor).toBe("rgb(241, 245, 249)");
    expect(theme.fontFamily.length).toBeGreaterThan(0);
    expect(theme.fontFamily.toLowerCase()).not.toContain("times");

    const heroPanelColor = await page.locator("[data-testid='login-hero-panel']").evaluate((element) => {
      return window.getComputedStyle(element).backgroundColor;
    });
    expect(heroPanelColor).toBe("rgba(12, 18, 30, 0.92)");

    const submitButton = page.locator("[data-testid='login-submit-button']");
    await expect(submitButton).toHaveCSS("background-color", "rgb(57, 192, 187)");
    await expect(submitButton).toHaveCSS("color", "rgb(6, 11, 20)");

    const emailInput = page.locator("[data-testid='login-email-input']");
    await expect(emailInput).toHaveCSS("background-color", "rgba(8, 13, 24, 0.7)");
    await expect(emailInput).toHaveCSS("color", "rgb(241, 245, 249)");

    await expect(page).toHaveScreenshot("login-page-login-mode.png", {
      animations: "disabled",
      fullPage: true,
    });
  });

  test("renders register mode with the correct active state and stable layout", async ({ page }) => {
    await page.getByTestId("register-mode-button").click();

    await expect(page.getByRole("heading", { name: "Create Account" })).toBeVisible();
    await expect(page.getByTestId("login-password-input")).toHaveAttribute("autocomplete", "new-password");

    const registerButton = page.getByTestId("register-mode-button");
    const loginButton = page.getByTestId("login-mode-button");

    await expect(registerButton).toHaveCSS("background-color", "rgb(57, 192, 187)");
    await expect(registerButton).toHaveCSS("color", "rgb(6, 11, 20)");
    await expect(loginButton).toHaveCSS("background-color", "rgb(18, 27, 43)");
    await expect(loginButton).toHaveCSS("color", "rgb(192, 205, 224)");

    await expect(page).toHaveScreenshot("login-page-register-mode.png", {
      animations: "disabled",
      fullPage: true,
    });
  });
});