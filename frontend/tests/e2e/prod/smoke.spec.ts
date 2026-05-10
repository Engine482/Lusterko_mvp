import { expect, test } from "@playwright/test";

// Non-destructive production smoke. Verifies that the deployed app
// renders the public surface — login, forgot-password, register —
// and that the unauthenticated nav contract holds (no burger / role
// switcher / logout leaks before sign-in). No POST, no PATCH, no
// logout: this suite must be safe to run against real production.

test("/ serves the public landing surface", async ({ page }) => {
  // Pre-P0.2 prod still shows the two-button landing page; post-P0.2 it
  // redirects to /login. Either is acceptable for the smoke check — we
  // only care that the brand is visible and there's no auth-leak.
  const response = await page.goto("/");
  expect(response?.ok()).toBeTruthy();
  await expect(page.locator(".app-shell__brand")).toBeVisible();
});

test("login page renders form fields", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator(".app-shell__brand")).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Пароль")).toBeVisible();
  await expect(page.getByRole("button", { name: /Увійти|Вхід/ })).toBeVisible();
});

test("forgot-password page renders", async ({ page }) => {
  await page.goto("/forgot-password");
  await expect(page).toHaveURL(/forgot-password/);
});

test("register surface renders something", async ({ page }) => {
  await page.goto("/register");
  await expect(
    page.getByRole("heading", { name: /Demo-реєстрація|Реєстрація недоступна/ }),
  ).toBeVisible();
});

const PUBLIC_ROUTES = ["/", "/login", "/forgot-password", "/register"];

for (const path of PUBLIC_ROUTES) {
  test(`public ${path} hides authenticated controls in prod`, async ({ page }) => {
    await page.goto(path);
    await expect(
      page.getByRole("button", { name: "Відкрити меню" }),
    ).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Вийти/ })).toHaveCount(0);
    await expect(page.locator(".app-shell__brand")).toBeVisible();
  });
}
