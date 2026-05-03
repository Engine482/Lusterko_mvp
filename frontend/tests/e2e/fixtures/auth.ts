import type { APIRequestContext, Page } from "@playwright/test";

export type DemoRole = "soldier" | "commander" | "medic_psych" | "admin";

export type DemoCreds = {
  email: string;
  password: string;
};

const apiBase =
  process.env.E2E_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";

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

// Logs in via the API directly so individual specs do not depend on the login UI.
export async function loginViaApi(request: APIRequestContext, creds = demoCreds()): Promise<void> {
  const res = await request.post(`${apiBase}/api/v1/auth/login`, {
    data: { email: creds.email, password: creds.password },
  });
  if (!res.ok()) {
    throw new Error(`login failed: ${res.status()} ${await res.text()}`);
  }
}

// Logs in via the UI form. Used when the test needs to assert on login UX.
export async function loginViaUi(page: Page, creds = demoCreds()): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(creds.email);
  await page.getByLabel("Пароль").fill(creds.password);
  await page.getByRole("button", { name: /Увійти|Вхід/ }).click();
}
