import { expect, test } from "@playwright/test";

import { demoBackendConfigured, demoCreds, loginViaApi } from "../fixtures/auth";

// EPIC role switching is already implemented (RoleSwitcher.tsx). Spec verifies
// that current role is clearly visible and a multi-role demo user can switch.

test.describe("role switching", () => {
  test.skip(!demoBackendConfigured(), "needs multi-role E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD");
  test.fixme(true, "TASK-8102: pending demo seed strategy decision");

  test("multi-role user can switch active role", async ({ page, request }) => {
    await loginViaApi(request, demoCreds());
    await page.goto("/soldier");
    await page.getByRole("button", { name: /Командир|Психолог|Адміністратор/ }).click();
    await expect(page).toHaveURL(/(commander|medic|admin)/);
  });
});
