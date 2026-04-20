import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  expect: {
    toHaveScreenshot: {
      pathTemplate: "{testDir}/{testFilePath}-snapshots/{arg}{-projectName}{ext}",
    },
  },
  use: {
    baseURL: "http://127.0.0.1:4174",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 4174 --strictPort",
    url: "http://127.0.0.1:4174/login",
    reuseExistingServer: false,
    timeout: 120000,
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
      },
    },
    {
      name: "msedge",
      use: {
        ...devices["Desktop Chrome"],
        channel: "msedge",
      },
    },
    {
      name: "mobile-chrome",
      use: {
        ...devices["Pixel 7"],
      },
    },
  ],
});