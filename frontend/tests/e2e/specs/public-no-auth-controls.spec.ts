import { expect, test } from "@playwright/test";

// Per Task A/B: before login the header must not expose role-switcher,
// settings, or logout. AppNav renders nothing when /me returns 401.

const PUBLIC_ROUTES = [
  "/",
  "/login",
  "/forgot-password",
  "/register",
  "/invite?token=demo-token",
];

for (const path of PUBLIC_ROUTES) {
  test(`public ${path} hides authenticated controls`, async ({ page }) => {
    await page.goto(path);
    await expect(
      page.getByRole("button", { name: "Відкрити меню" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("button", { name: /Вийти/ }),
    ).toHaveCount(0);
    // Brand stays visible.
    await expect(page.locator(".app-shell__brand")).toBeVisible();
  });
}
