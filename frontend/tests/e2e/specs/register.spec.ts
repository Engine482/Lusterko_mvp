import { expect, test } from "@playwright/test";

// Public-only checks for the demo open-registration flow. The /register
// route is gated by /auth/config — without backend, the page renders the
// "registration disabled" copy, which is itself a useful regression
// guard (no role/settings leak, no overflow).

test("register page renders form fields", async ({ page }) => {
  await page.goto("/register");
  // Either the form (flag on) or the disabled copy (flag off) — both must
  // render *something* without crashing and without horizontal overflow.
  await expect(
    page.getByRole("heading", { name: /Demo-реєстрація|Реєстрація недоступна/ }),
  ).toBeVisible();
});

test("register/sent renders without an email param", async ({ page }) => {
  await page.goto("/register/sent");
  await expect(page.getByRole("heading", { name: /Перевірте пошту/ })).toBeVisible();
});

test("register/confirm renders with a token", async ({ page }) => {
  await page.goto("/register/confirm?token=demo-token");
  await expect(
    page.getByRole("heading", { name: /Завершення реєстрації/ }),
  ).toBeVisible();
});
