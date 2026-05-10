import { expect, test } from "@playwright/test";

import { demoBackendConfigured, loginViaApi } from "../fixtures/auth";

// EPIC-83 — Logout. Currently no logout UI exists in AppShell; spec encodes
// the expected end state. Will pass once TASK-8301..8303 ship.

test.describe("logout", () => {
  test.skip(!demoBackendConfigured(), "needs E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD + backend up");

  test("logout is reachable from app shell burger menu", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/soldier");
    await page.getByRole("button", { name: "Відкрити меню" }).click();
    await expect(page.getByRole("menuitem", { name: "Вийти" })).toBeVisible();
  });

  test("clicking logout clears session and redirects to /login", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/soldier");
    await page.getByRole("button", { name: "Відкрити меню" }).click();
    await page.getByRole("menuitem", { name: "Вийти" }).click();
    await expect(page).toHaveURL(/\/login/);
  });

  // TASK-9304 (follow-up): client-side auth gate. Currently, after logout
  // the backend rejects API calls (so no real data leaks), but the frontend
  // doesn't redirect away from protected URLs on its own. Adding a Next
  // middleware that reads the session cookie is the natural fix, but the
  // cookie is set by the backend on a different origin in prod (Railway
  // frontend vs. backend domain) and would never reach the middleware
  // there — needs a cookie-bridging plan before shipping the gate.
  test.fixme(true, "TASK-9304: client-side auth gate not implemented");

  test("after logout, protected route redirects to login", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/soldier");
    await page.getByRole("button", { name: "Відкрити меню" }).click();
    await page.getByRole("menuitem", { name: "Вийти" }).click();
    await expect(page).toHaveURL(/\/login/);
    await page.goto("/soldier");
    await expect(page).toHaveURL(/\/login/);
  });

  test("after logout, browser back does not reveal protected content", async ({
    page,
    request,
  }) => {
    await loginViaApi(request, page);
    await page.goto("/soldier");
    await page.getByRole("button", { name: "Відкрити меню" }).click();
    await page.getByRole("menuitem", { name: "Вийти" }).click();
    await expect(page).toHaveURL(/\/login/);
    await page.goBack();
    await expect(page).toHaveURL(/\/login/);
  });
});
