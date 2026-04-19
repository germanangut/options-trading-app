import type { Page, Route } from "@playwright/test";

import { mockCurrentUser, mockLatestScanResult } from "../fixtures/appVisualFixtures";

const AUTH_TOKEN_STORAGE_KEY = "options-platform.auth-token";

type AuthenticatedPageOptions = {
  currentUser?: unknown;
  latestScan?: unknown;
};

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function stabilizePageRendering(page: Page) {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation: none !important;
        transition: none !important;
        caret-color: transparent !important;
      }
    `,
  });
}

export async function openAuthenticatedPage(page: Page, path: string, options: AuthenticatedPageOptions = {}) {
  await page.addInitScript((tokenKey: string) => {
    window.localStorage.clear();
    window.sessionStorage.clear();
    window.localStorage.setItem(tokenKey, "visual-test-token");
  }, AUTH_TOKEN_STORAGE_KEY);

  await page.route("**/auth/me", async (route) => {
    await fulfillJson(route, options.currentUser ?? mockCurrentUser);
  });

  await page.route("**/scans/latest", async (route) => {
    await fulfillJson(route, options.latestScan ?? mockLatestScanResult);
  });

  await page.goto(path);
  await stabilizePageRendering(page);
}