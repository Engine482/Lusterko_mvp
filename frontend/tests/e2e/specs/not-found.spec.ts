import { expect, test } from "@playwright/test";

// 404 page sanity. Today expected to FAIL — Next.js default 404 has English copy
// and no "back to main" CTA. Becomes green after TASK-8905 (custom not-found page).
test("404 page shows Ukrainian copy and a way back home", async ({ page }) => {
  const res = await page.goto("/lusterko-no-such-route-for-e2e");
  expect(res?.status()).toBe(404);
  await expect(page.getByText(/Сторінку не знайдено/)).toBeVisible();
  await expect(page.getByRole("link", { name: /головну/i })).toBeVisible();
});
