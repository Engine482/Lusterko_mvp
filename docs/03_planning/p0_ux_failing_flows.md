# P0-UX-1 — Failing flows baseline

> Captured 2026-05-03 against `frontend/` Next.js 16 dev build, no backend running. Source: `pnpm test:e2e --project=desktop-chromium --project=mobile-iphone-se --project=tablet-ipad-mini`.

> Цей файл — снапшот стану перед стабілізацією. Не оновлювати; нові капчі писати в окремих файлах із датою.

## Run summary
- **15 passed**: public shell smoke (login + forgot-password), no horizontal overflow on `/login` and `/forgot-password` across desktop/iPhone SE/iPad Mini.
- **3 failed**: 404 page across 3 viewports — Next default 404 has English copy, no "back home" link.
- **33 skipped**: backend-dependent specs (logout / settings / military-baseline / role-switch). Marked `test.fixme` with TASK-IDs; will switch to live as P0-UX-1 progresses.

## Capture matrix
| Spec | Status | TASK-ID |
| --- | --- | --- |
| `public-shell.spec.ts` — login form structure | ✅ pass | — |
| `public-shell.spec.ts` — forgot-password renders | ✅ pass | — |
| `no-horizontal-overflow.spec.ts` — `/login` | ✅ pass | — |
| `no-horizontal-overflow.spec.ts` — `/forgot-password` | ✅ pass | — |
| `not-found.spec.ts` — Ukrainian 404 + back-home link | ❌ fail | TASK-8905 |
| `logout.spec.ts` — logout button in header | ⏭ fixme | TASK-8301 |
| `logout.spec.ts` — logout clears session | ⏭ fixme | TASK-8302 |
| `logout.spec.ts` — protected route redirect after logout | ⏭ fixme | TASK-8303 |
| `logout.spec.ts` — back button does not reveal protected | ⏭ fixme | TASK-8303 |
| `settings.spec.ts` — change display name | ⏭ fixme | TASK-8403 |
| `settings.spec.ts` — security form fields visible | ⏭ fixme | TASK-8404 |
| `settings.spec.ts` — wrong current password error | ⏭ fixme | TASK-8404 |
| `military-baseline.spec.ts` — reaction starts via Start | ⏭ fixme | TASK-8201 |
| `military-baseline.spec.ts` — 10 trials + save | ⏭ fixme | TASK-8203 |
| `military-baseline.spec.ts` — baseline e2e | ⏭ fixme | TASK-8204 |
| `role-switch.spec.ts` — multi-role switch | ⏭ fixme | TASK-8102 |

## Verified bugs found by audit (not by tests yet)
- **Reaction-time test does not start** — `frontend/components/cognitive/ReactionTest.tsx:52` returns early on clicks while `phase === "instructions"`. There is no Start button, so `startTrial()` is never invoked. Fix: explicit Start affordance OR treat first instructions-phase click as begin-trial. Owner: TASK-8201.
- **No logout UI** — `/api/v1/auth/logout` exists in `frontend/lib/api/auth.ts:45`, but `AppShell` exposes only the `RoleSwitcher`. Owner: TASK-8301.
- **No settings routes** — neither `/settings/profile` nor `/settings/security` exist; backend has no `/auth/password/change` (in-session) or full_name update endpoint. Owners: TASK-8401..8407.
- **Default 404 page** — Next.js default 404 with English copy. Owner: TASK-8905.
- **Minimal styling** — `app/globals.css` has no design tokens, no media queries, no responsive container constraints. Owners: EPIC-86 + EPIC-87.

## How to re-run
```sh
cd frontend
pnpm dev                     # in another shell, or background
pnpm test:e2e                # all viewports
pnpm test:e2e --project=desktop-chromium  # one viewport only
pnpm test:e2e:report         # open HTML report
```

To enable backend-dependent specs:
```sh
# 1. Boot DB + migrate + seed admin with known password
make db-up && make db-migrate
BOOTSTRAP_ADMIN_PASSWORD='ChangeMeAdmin!23' \
  ADMIN_EMAIL=e2e-admin@lusterko.local \
  BOOTSTRAP_USER_ROLES=admin,soldier,commander,medic_psych \
  make seed
# 2. Boot backend
make run-backend             # in another shell
# 3. Re-run with creds exported
E2E_DEMO_EMAIL=e2e-admin@lusterko.local \
E2E_DEMO_PASSWORD='ChangeMeAdmin!23' \
  pnpm test:e2e
```

Removing `test.fixme(true, ...)` lines as TASK-IDs ship is part of each acceptance.
