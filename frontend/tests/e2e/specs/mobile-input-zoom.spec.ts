import { expect, test } from "@playwright/test";

// iOS Safari triggers a focus-zoom on any input/select/textarea whose
// computed font-size is below 16px. The fix is enforced globally in
// app/globals.css (`input, select, textarea { font-size: max(16px, 1rem) }`);
// this spec asserts it stays in place across the public auth surfaces.

const ROUTES = [
  "/login",
  "/forgot-password",
  "/reset-password?token=demo-token",
  "/invite?token=demo-token",
  "/register",
  "/register/confirm?token=demo-token",
];

for (const path of ROUTES) {
  test(`inputs on ${path} are at least 16px to prevent iOS zoom`, async ({ page }) => {
    await page.goto(path);
    const tooSmall = await page.evaluate(() => {
      const offenders: { selector: string; size: number }[] = [];
      document
        .querySelectorAll<HTMLElement>("input, select, textarea")
        .forEach((el) => {
          const size = parseFloat(getComputedStyle(el).fontSize);
          if (Number.isFinite(size) && size < 16) {
            offenders.push({ selector: el.tagName.toLowerCase(), size });
          }
        });
      return offenders;
    });
    expect(tooSmall, `inputs below 16px on ${path}: ${JSON.stringify(tooSmall)}`).toHaveLength(
      0,
    );
  });
}
