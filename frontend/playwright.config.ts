import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3001";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],
  // Per the project's "Next 16 Turbopack vs Playwright" note: the e2e
  // suite must run against `pnpm start` (production mode), not `pnpm dev`.
  // CI builds the app first; locally the same `pnpm build` is required
  // before `pnpm test:smoke` (or set E2E_NO_WEBSERVER=1 to manage the
  // server yourself). `reuseExistingServer` lets devs keep one server
  // running between iterations.
  webServer: process.env.E2E_NO_WEBSERVER
    ? undefined
    : {
        command: "pnpm exec next start -p 3001",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "desktop-webkit", use: { ...devices["Desktop Safari"] } },
    { name: "mobile-iphone-14-pro-max", use: { ...devices["iPhone 14 Pro Max"] } },
    { name: "mobile-iphone-se", use: { ...devices["iPhone SE"] } },
    { name: "mobile-pixel-7", use: { ...devices["Pixel 7"] } },
    { name: "tablet-ipad-mini", use: { ...devices["iPad Mini"] } },
    { name: "tablet-ipad-pro-11", use: { ...devices["iPad Pro 11"] } },
    {
      name: "tablet-ipad-pro-11-landscape",
      use: { ...devices["iPad Pro 11 landscape"] },
    },
    { name: "tablet-ipad-pro-12-landscape", use: { ...devices["iPad Pro 12 landscape"] } },
  ],
});
