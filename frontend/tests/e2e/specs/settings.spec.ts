import { expect, test } from "@playwright/test";

import { demoBackendConfigured, demoCreds, loginViaApi } from "../fixtures/auth";

// EPIC-84 — Settings (display name + password change).
// Routes don't exist yet; specs encode the expected UX.

test.describe("settings/profile", () => {
  test.skip(!demoBackendConfigured(), "needs E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD + backend up");

  test("user can change display name", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/settings/profile");
    const newName = `Демо Користувач ${Date.now()}`;
    await page.getByLabel(/Імʼя|Ім'я|Display name/i).fill(newName);
    await page.getByRole("button", { name: /Зберегти|Save/ }).click();
    await expect(page.getByText(/Імʼя оновлено|Ім'я оновлено/)).toBeVisible();
    await page.reload();
    await expect(page.getByLabel(/Імʼя|Ім'я/i)).toHaveValue(newName);
  });
});

test.describe("settings/security", () => {
  test.skip(!demoBackendConfigured(), "needs E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD + backend up");

  test("user sees current/new/confirm fields", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/settings/security");
    await expect(page.getByLabel(/Поточний пароль/)).toBeVisible();
    await expect(page.getByLabel(/Новий пароль/)).toBeVisible();
    await expect(page.getByLabel(/Підтвердіть/)).toBeVisible();
  });

  test("wrong current password shows readable Ukrainian error", async ({ page, request }) => {
    await loginViaApi(request, page);
    await page.goto("/settings/security");
    await page.getByLabel(/Поточний пароль/).fill("definitely-wrong-password-xyz");
    await page.getByLabel(/Новий пароль/).fill("NewStrongPass!123");
    await page.getByLabel(/Підтвердіть/).fill("NewStrongPass!123");
    await page.getByRole("button", { name: /Зберегти|Змінити/ }).click();
    await expect(page.getByText(/Перевірте поточний пароль/)).toBeVisible();
  });
});
