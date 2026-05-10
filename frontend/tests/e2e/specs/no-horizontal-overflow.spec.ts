import { expect, test } from "@playwright/test";

// Layout sanity for routes runnable without backend.
// Asserts the document does not scroll horizontally — the key iPhone Safari
// failure mode the appendix calls out (lusterko_p0_ui_ux_demo_hardening §6).
//
// Authed routes (dashboards, baseline, settings) are guarded in their own
// specs and require a seeded backend; this file stays public-only so it runs
// in any environment.
const ROUTES = [
  "/login",
  "/forgot-password",
  "/reset-password?token=demo-token",
  "/invite?token=demo-token",
  "/register",
  "/register/sent?email=test%40example.com",
  "/register/confirm?token=demo-token",
  "/this-route-does-not-exist",
];

for (const path of ROUTES) {
  test(`no horizontal overflow on ${path}`, async ({ page }) => {
    await page.goto(path);
    const overflow = await page.evaluate(() => {
      const doc = document.documentElement;
      return doc.scrollWidth - doc.clientWidth;
    });
    expect(overflow, `${path} document scrolls horizontally by ${overflow}px`).toBeLessThanOrEqual(
      1,
    );
  });
}
