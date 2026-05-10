import { expect, test } from "@playwright/test";

// Backend-independent baseline: public routes render shell + form structure.
// These should be green today; if they go red, the AppShell or auth pages regressed.

test("login page renders header brand and form", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator(".app-shell__brand")).toBeVisible();
  // Product intro above the form (P0.2).
  await expect(page.getByRole("heading", { name: "Люстерко" })).toBeVisible();
  await expect(page.getByText(/MVP системи моніторингу/)).toBeVisible();
  await expect(page.getByRole("heading", { name: /Вхід/ })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Пароль")).toBeVisible();
  await expect(page.getByRole("button", { name: /Увійти|Вхід/ })).toBeVisible();
});

test("forgot-password page renders", async ({ page }) => {
  await page.goto("/forgot-password");
  await expect(page).toHaveURL(/forgot-password/);
});
