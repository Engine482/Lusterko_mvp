import { expect, test } from "@playwright/test";

import { demoBackendConfigured, loginViaApi } from "../fixtures/auth";

// Role switching now lives in the burger nav: open menu → "Змінити роль" → /role.

test.describe("role switching", () => {
  test.skip(!demoBackendConfigured(), "needs multi-role E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD");

  test("multi-role user can switch active role", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/admin");
    await page.getByRole("button", { name: "Відкрити меню" }).click();
    await page.getByRole("menuitem", { name: "Змінити роль" }).click();
    await expect(page).toHaveURL(/\/role/);
    await page.getByRole("button", { name: /Командир/ }).click();
    await expect(page).toHaveURL(/\/commander/);
  });
});
