import { expect, type Page } from "@playwright/test";

export type DemoRole = "soldier" | "commander" | "medic_psych" | "admin";

export type DemoCreds = {
  email: string;
  password: string;
};

const apiBase =
  process.env.E2E_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";

const DEFAULT_ROLE: DemoRole =
  (process.env.E2E_DEMO_ROLE as DemoRole | undefined) ?? "admin";

export function demoBackendConfigured(): boolean {
  return Boolean(process.env.E2E_DEMO_EMAIL && process.env.E2E_DEMO_PASSWORD);
}

export function demoCreds(): DemoCreds {
  const email = process.env.E2E_DEMO_EMAIL;
  const password = process.env.E2E_DEMO_PASSWORD;
  if (!email || !password) {
    throw new Error(
      "E2E_DEMO_EMAIL/E2E_DEMO_PASSWORD not set. Boot backend with seeded admin (BOOTSTRAP_ADMIN_PASSWORD) and export both before running auth-dependent specs.",
    );
  }
  return { email, password };
}

// Logs in by issuing the same fetch the frontend would issue, but from
// inside the page context — that way the browser stores the Set-Cookie
// against the page's cookie jar (vs Playwright's APIRequestContext, whose
// jar doesn't auto-merge into the browser context across origins).
//
// Bypassing the UI sidesteps a Next.js 16 + React 19 quirk in Turbopack
// dev where the `<form onSubmit>` handler can take a long time to attach
// after route load, causing the form to natively submit as GET to /login?.
export async function loginViaApi(
  _request: unknown,
  page: Page,
  creds = demoCreds(),
  role: DemoRole = DEFAULT_ROLE,
): Promise<void> {
  await page.goto("/login");
  await page.evaluate(
    async ({ apiBase, creds }) => {
      const login = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: creds.email, password: creds.password }),
      });
      if (!login.ok) {
        throw new Error(`login ${login.status}: ${await login.text()}`);
      }
    },
    { apiBase, creds },
  );

  // Pick an active role for multi-role users so subsequent navigation
  // doesn't get bounced through /role.
  const roleNeeded = await page.evaluate(
    async ({ apiBase }) => {
      const me = await fetch(`${apiBase}/api/v1/auth/me`, { credentials: "include" });
      const data = (await me.json()) as {
        data?: { roles: string[]; role_selection_required: boolean };
      };
      return data.data ?? null;
    },
    { apiBase },
  );

  if (roleNeeded?.role_selection_required) {
    const desired = roleNeeded.roles.includes(role) ? role : roleNeeded.roles[0];
    await page.evaluate(
      async ({ apiBase, role }) => {
        const res = await fetch(`${apiBase}/api/v1/auth/select-role`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role }),
        });
        if (!res.ok) {
          throw new Error(`select-role ${res.status}: ${await res.text()}`);
        }
      },
      { apiBase, role: desired },
    );
  }
}

// Logs in via the UI form. Used when the test specifically asserts on
// login UX. Note: in Turbopack dev, hydration timing can defeat plain
// click-to-submit; specs that just need an authed session should prefer
// loginViaApi above.
export async function loginViaUi(page: Page, creds = demoCreds()): Promise<void> {
  await page.goto("/login", { waitUntil: "networkidle" });
  const submit = page.getByRole("button", { name: /Увійти|Вхід/ });
  await expect(submit).toBeEnabled();
  await page.getByLabel("Email").fill(creds.email);
  await page.getByLabel("Пароль").fill(creds.password);
  await submit.click();
}
