import { expect, test } from "@playwright/test";

// TASK-8905 — custom Ukrainian 404 page.
test("404 page shows Ukrainian copy and a way back home", async ({ page }) => {
  const res = await page.goto("/lusterko-no-such-route-for-e2e");
  expect(res?.status()).toBe(404);
  await expect(page.getByText(/Сторінку не знайдено/)).toBeVisible();
  await expect(page.getByRole("link", { name: /головну/i })).toBeVisible();
});
