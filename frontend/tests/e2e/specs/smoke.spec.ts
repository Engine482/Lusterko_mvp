import { expect, test } from "@playwright/test";

// Sanity check that the runner reaches the app and renders the brand mark.
// Does not depend on backend — only checks public shell on the login route.
test("login route renders the Lusterko brand", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator(".app-shell__brand")).toBeVisible();
});
