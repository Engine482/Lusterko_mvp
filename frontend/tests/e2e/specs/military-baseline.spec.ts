import { expect, test } from "@playwright/test";

import { demoBackendConfigured, demoCreds, loginViaApi } from "../fixtures/auth";

// EPIC-82 — Reaction-time test currently does not start (ReactionTest.tsx:52
// returns early on instructions-phase clicks; no Start button). This spec
// captures the expected post-fix behavior.

test.describe("military baseline — reaction-time", () => {
  test.skip(!demoBackendConfigured(), "needs E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD + backend up");
  test.fixme(true, "TASK-8201: reaction-time does not start in current build");

  test("reaction test starts via explicit Start affordance", async ({ page, request }) => {
    await loginViaApi(request, demoCreds());
    await page.goto("/soldier/baseline/reaction");
    await page.getByRole("button", { name: /Почати|Start/ }).click();
    // Should leave instructions phase: either "Чекайте" or "Натисніть!" appears.
    await expect(page.getByText(/Чекайте|Натисніть!/)).toBeVisible({ timeout: 5_000 });
  });

  test("reaction test completes 10 trials and saves result", async ({ page, request }) => {
    await loginViaApi(request, demoCreds());
    await page.goto("/soldier/baseline/reaction");
    await page.getByRole("button", { name: /Почати|Start/ }).click();
    for (let i = 0; i < 10; i += 1) {
      await page.getByText(/Натисніть!/).waitFor({ timeout: 5_000 });
      await page.locator("body").click();
      // Allow component state machine to advance.
      await page.waitForTimeout(50);
    }
    await expect(page.getByText(/Тест завершено/)).toBeVisible();
    // Reaction submission redirects to gonogo step.
    await expect(page).toHaveURL(/baseline\/gonogo/);
  });
});

test.describe("military baseline — end-to-end completion", () => {
  test.skip(!demoBackendConfigured(), "needs E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD + backend up");
  test.fixme(true, "TASK-8204: blocked by reaction-time fix");

  test("baseline can be completed end-to-end", async ({ page, request }) => {
    await loginViaApi(request, demoCreds());
    await page.goto("/soldier/baseline");
    // Walk every baseline step. Concrete selectors are filled in by the dev
    // implementing TASK-8204 — leaving structural skeleton here.
    await expect(page.getByRole("heading", { name: /baseline|оцінка/i })).toBeVisible();
  });
});
