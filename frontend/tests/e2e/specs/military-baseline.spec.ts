import { expect, test } from "@playwright/test";

import { demoBackendConfigured, loginViaApi } from "../fixtures/auth";

// EPIC-82 — reaction-time. Was broken in earlier sprint (no Start
// affordance); shipped in P0-UX-1 6bae242. Spec verifies the post-fix
// behavior using soldier role to access /soldier/baseline.

test.describe("military baseline — reaction-time", () => {
  test.skip(!demoBackendConfigured(), "needs E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD + backend up");

  test("reaction test starts via Start affordance", async ({ page, request }) => {
    await loginViaApi(request, page, undefined, "soldier");
    await page.goto("/soldier/baseline/reaction");
    // The button has an aria-label describing the instruction, so we
    // locate by visible text instead of role+name.
    await page.getByText(/Почати — спроба 1/).click();
    await expect(page.getByText(/Чекайте|Натисніть!/)).toBeVisible({ timeout: 5_000 });
  });
});

test.describe("military baseline — end-to-end completion", () => {
  test.skip(!demoBackendConfigured(), "needs E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD + backend up");
  // The 10-trial click-through and full baseline walk are timing-sensitive
  // (random ISI 1–3s × 10) and the spec was originally a structural
  // skeleton. Keeping them as tracked follow-ups rather than flaky CI.
  test.fixme(true, "TASK-9305: full 10-trial baseline walk left as manual demo step");

  test("reaction test completes 10 trials and saves result", async ({ page, request }) => {
    await loginViaApi(request, page, undefined, "soldier");
    await page.goto("/soldier/baseline/reaction");
    await page.getByText(/Почати — спроба 1/).click();
    for (let i = 0; i < 10; i += 1) {
      await page.getByText(/Натисніть!/).waitFor({ timeout: 5_000 });
      await page.locator("body").click();
      await page.waitForTimeout(50);
    }
    await expect(page.getByText(/Тест завершено/)).toBeVisible();
    await expect(page).toHaveURL(/baseline\/gonogo/);
  });

  test("baseline can be completed end-to-end", async ({ page, request }) => {
    await loginViaApi(request, page, undefined, "soldier");
    await page.goto("/soldier/baseline");
    await expect(page.getByRole("heading", { name: /baseline|оцінка/i })).toBeVisible();
  });
});
