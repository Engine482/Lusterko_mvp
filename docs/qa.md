# QA Runbook

How to validate Lusterko before a release and what to expect from each
automated check. The flow is short on purpose so manual QA stays focused
on product decisions, not regression hunting.

## Quick checklist

```text
[ ] Backend: ruff + mypy + pytest green
[ ] Frontend: lint + tsc green
[ ] Frontend smoke (Playwright) green on desktop + mobile
[ ] Production smoke green against the deployed URL
```

If any of the above fail, do not ship. CI gates the first three on
every push; the production smoke is a manual one-liner.

## Backend checks

```bash
cd backend
uv sync --all-extras --dev
uv run ruff check .
uv run mypy app
uv run pytest -q
```

`pytest` needs Postgres on `localhost:5432` (or `TEST_DATABASE_URL=...`).
The CI workflow stands one up via `services.postgres`.

## Frontend checks

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm lint
pnpm exec tsc --noEmit
```

These are non-negotiable: CI fails the `frontend` job if either is red.

## Frontend smoke (Playwright, local)

The smoke run hits the production-mode `next start` build. **Do not run
it against `next dev`** — the project's known issue with Next 16
Turbopack means `onSubmit` handlers attach too late and form-submit
specs flake.

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm exec playwright install --with-deps chromium webkit
pnpm build
pnpm test:smoke
```

`playwright.config.ts` brings up `next start -p 3001` automatically via
`webServer`. Set `E2E_NO_WEBSERVER=1` if you already have a server
running and want Playwright to reuse it.

The smoke set covers the public surface only (no auth required):

- `tests/e2e/specs/smoke.spec.ts`
- `tests/e2e/specs/public-shell.spec.ts`
- `tests/e2e/specs/public-no-auth-controls.spec.ts`
- `tests/e2e/specs/register.spec.ts`
- `tests/e2e/specs/not-found.spec.ts`
- `tests/e2e/specs/no-horizontal-overflow.spec.ts`

It runs on `desktop-chromium` AND `mobile-iphone-se` so menu-overflow
and horizontal-scroll regressions surface on the most common phone
viewport.

## Frontend smoke in CI

The `smoke-e2e` GitHub Actions job in `.github/workflows/ci.yml` runs
the same `pnpm test:smoke` after the lint job goes green. On failure
the playwright HTML report is uploaded as an artifact (7-day retention)
under the name `playwright-report` — open it locally with
`pnpm test:e2e:report`.

## Production smoke

Run after every deploy. It is **non-destructive** — no logout, no
PATCH, no POST that mutates real data — and safe against the live
Railway environment.

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm exec playwright install --with-deps chromium webkit
PROD_BASE_URL=https://lusterko.motornyi.com pnpm test:prod-smoke
```

Override `PROD_BASE_URL` to point at any other deployment (staging,
preview environments, etc.). Specs live in
`frontend/tests/e2e/prod/smoke.spec.ts` and run on both `desktop-chromium`
and `mobile-iphone-se`.

The HTML report lands in `frontend/playwright-report-prod/`.

## Demo accounts

The seeded `Демо-взвод` includes:

- 1 commander (`commander@demo-platoon.lusterko.local`)
- 1 psychologist (`medic@demo-platoon.lusterko.local`)
- 30 soldiers (`boets01..30@demo-platoon.lusterko.local`) split 10 / 10 / 10
  across green / yellow / red risk states with ~4 weeks of back-dated
  history.

Self-registered testers (via `/register`) get all three demo roles
(`soldier + commander + medic_psych`) and are auto-attached to
`Демо-взвод` so commander/medic dashboards render data on first login.

**Local credentials live outside the repo.** Do not commit demo
passwords or invite tokens. For production smoke we only need
unauthenticated routes.

## Re-running the demo seed

The seed script is idempotent and refuses on `APP_ENV=production`
unless `FORCE=1` is also set:

```bash
cd backend
DATABASE_URL=... uv run python -m scripts.seed_demo_unit
DATABASE_URL=... FORCE=1 APP_ENV=production uv run python -m scripts.seed_demo_unit
```

To rebuild from scratch:

```bash
DATABASE_URL=... uv run python -m scripts.seed_demo_unit --reset-demo-data
```

Reset only deletes rows that belong to the `@demo-platoon.lusterko.local`
domain — bootstrap admin and other seed data are untouched.

## Known limitations

- The smoke suites cover the public surface only. Authenticated flows
  (commander dashboard, medic queue, manual case actions) still rely
  on manual review until a backend container is wired into CI.
- WebKit is installed in CI for `mobile-iphone-se`, but mobile Safari
  on real devices can drift from Playwright's emulation; treat the
  mobile project as a regression net, not a substitute for hand-testing.
- The production smoke does not verify SMTP delivery. Check Railway
  logs for `mailer_init` to confirm the active mailer strategy and
  watch `demo_registration_email_*` audit events to know whether sends
  actually went out.
