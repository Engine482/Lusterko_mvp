import { expect, test } from "@playwright/test";

import { demoBackendConfigured, loginViaApi } from "../fixtures/auth";

// EPIC role switching is already implemented (RoleSwitcher.tsx). Spec verifies
// that current role is clearly visible and a multi-role demo user can switch.

test.describe("role switching", () => {
  test.skip(!demoBackendConfigured(), "needs multi-role E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD");

  test("multi-role user can switch active role", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/admin");
    // Open the role-switcher menu, then pick a different role.
    await page.getByRole("button", { name: /Перемкнути активну роль/ }).click();
    await page.getByRole("menuitem", { name: /Командир/ }).click();
    await expect(page).toHaveURL(/\/commander/);
  });
});
