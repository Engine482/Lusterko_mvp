import { expect, test } from "@playwright/test";

// Layout sanity for public routes — runnable without backend.
// Asserts the document does not scroll horizontally (a key iPhone Safari
// failure mode the appendix calls out).
const ROUTES = ["/login", "/forgot-password"];

for (const path of ROUTES) {
  test(`no horizontal overflow on ${path}`, async ({ page }) => {
    await page.goto(path);
    const overflow = await page.evaluate(() => {
      const doc = document.documentElement;
      return doc.scrollWidth - doc.clientWidth;
    });
    expect(overflow, `${path} document scrolls horizontally by ${overflow}px`).toBeLessThanOrEqual(
      1,
    );
  });
}
