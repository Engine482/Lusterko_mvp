import { defineConfig, devices } from "@playwright/test";

// Non-destructive production smoke runner. Hits the deployed Railway app
// (or any URL passed via PROD_BASE_URL) and never starts a local server.
// Keep specs in tests/e2e/prod/ strictly read-only — no logout, no PATCH,
// no POST that mutates real data.
const baseURL = process.env.PROD_BASE_URL ?? "https://lusterko.motornyi.com";

export default defineConfig({
  testDir: "./tests/e2e/prod",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report-prod", open: "never" }],
  ],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  // Production runs against the deployed app; no webServer.
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile-iphone-se", use: { ...devices["iPhone SE"] } },
  ],
});
