# Lusterko — Development Backlog UX Appendix v1

> Додаток до `Lusterko_Development_Backlog_v1.md`. Основний P0 беклог залишається статичним — цей файл містить задачі етапу **UI/UX Stabilization & Demo Hardening** (див. `lusterko_p0_ui_ux_demo_hardening.md`).

> Нумерація: `TASK-80xx` = Sprint P0-UX-1, `TASK-81xx` = Sprint P0-UX-2, `TASK-82xx` = Sprint P0-UX-3.

> Source of truth для прогресу — git log + sprint commits (`feat(sprint-p0-ux-N): ...`). Цей файл не оновлюється статусами.

## Sprint P0-UX-1 — Stabilization
### EPIC-80 Test harness bootstrap
- TASK-8001 — Підняти Playwright у `frontend/`, додати `pnpm test:e2e`
- TASK-8002 — Сконфігурувати viewports: Desktop Chromium, Mobile Safari/WebKit, iPhone Pro Max, iPhone SE, Pixel, iPad Mini portrait, iPad 11" portrait+landscape, iPad Pro 12.9" landscape
- TASK-8003 — Додати helper `loginAs(role)` для seed-користувачів демо-середовища
- TASK-8004 — Налаштувати CI job `frontend-e2e` (опційно, якщо не блокує)

### EPIC-81 Failing-flow capture
- TASK-8101 — Spec: auth (login + logout + protected redirect + browser-back-after-logout)
- TASK-8102 — Spec: role switching
- TASK-8103 — Spec: settings access (display name change + password change)
- TASK-8104 — Spec: military baseline end-to-end з reaction-test
- TASK-8105 — Spec: mobile/tablet layout — no horizontal overflow на ключових екранах
- TASK-8106 — Зафіксувати baseline pass/fail матрицю в `docs/03_planning/p0_ux_failing_flows.md`

### EPIC-82 Critical blocker fix — reaction-time test
- TASK-8201 — Полагодити старт у `frontend/components/cognitive/ReactionTest.tsx`: explicit Start кнопка АБО клік у `instructions` ініціює `startTrial()`
- TASK-8202 — Перевірити touch handler-и (mobile Safari/iPad)
- TASK-8203 — Покрити Playwright-тестом старт + 10 спроб + збереження результату
- TASK-8204 — Перевірити, що військовий baseline проходиться end-to-end після фіксу

### EPIC-83 Account UX — logout
- TASK-8301 — Додати logout у `AppShell` header (поряд з RoleSwitcher) або у user menu
- TASK-8302 — Виклик `/api/v1/auth/logout`, очистити cookie/session, redirect на `/login`
- TASK-8303 — Перевірити: protected routes redirect-ять; browser Back не показує приватний контент

### EPIC-84 Account UX — settings
- TASK-8401 — Backend: `POST /api/v1/auth/password/change` (current_password + new_password, argon2id verify+rehash, audit `password_changed`)
- TASK-8402 — Backend: `PATCH /api/v1/auth/me` для зміни `full_name` (display name)
- TASK-8403 — Frontend: route `/settings/profile` з формою display name
- TASK-8404 — Frontend: route `/settings/security` з формою password change (current + new + confirm)
- TASK-8405 — Frontend: посилання на `/settings` у AppShell user menu / header
- TASK-8406 — Validation + Ukrainian error/success стани на обох формах
- TASK-8407 — Tests: backend integration (success / wrong current / weak new / rate-limit) + Playwright e2e

### EPIC-85 Mobile/tablet layout — critical blockers
- TASK-8501 — Додати `<meta viewport>` (перевірити в `app/layout.tsx`)
- TASK-8502 — Виправити horizontal overflow на dashboard / forms / baseline (use Playwright fail report як список)
- TASK-8503 — Touch targets ≥ 44px на ключових кнопках baseline + reaction
- TASK-8504 — Form max-width 420–480px, dashboard max-width 1100–1280px, page padding 16/24/32

---

## Sprint P0-UX-2 — Presentation polish
### EPIC-86 Design tokens
- TASK-8601 — Створити `frontend/app/tokens.css` з токенами (bg/card/border/accent/text/status), див. `lusterko_p0_ui_ux_demo_hardening.md` §7.2
- TASK-8602 — Перенести існуючі стилі в `globals.css` на токени; уникнути inline-стилів у key компонентах
- TASK-8603 — Inter як основний font + system fallback; base 16px; mobile body min 16px
- TASK-8604 — Card radius 16–20px, button 12px, input 10–12px

### EPIC-87 Lightweight redesign
- TASK-8701 — Auth screens (login/invite/forgot/reset) під clinical-tactical style
- TASK-8702 — AppShell header + footer (project identity)
- TASK-8703 — Dashboards (soldier home, commander, medic, admin)
- TASK-8704 — Baseline flow + reaction screen + go/no-go
- TASK-8705 — Settings (profile/security)
- TASK-8706 — Role switch UI
- TASK-8707 — Buttons / forms / cards / alerts shared primitives

### EPIC-88 Identity & metadata
- TASK-8801 — Favicon + apple-touch-icon (тимчасова чиста версія, концепт = brain cross-section mirror)
- TASK-8802 — `metadata` у `app/layout.tsx`: title "Люстерко — моніторинг стану особового складу", description, theme-color `#0B1120`, OG tags
- TASK-8803 — Footer: "Люстерко MVP · Volodymyr Motornyi · 2026" + версійний бейдж "P0 · v0.1.0 · demo"
- TASK-8804 — About modal/page з коротким поясненням системи
- TASK-8805 — Demo/privacy disclaimer (placement у footer + login)

### EPIC-89 UI states
- TASK-8901 — Empty states з Ukrainian copy (baseline empty, no subordinates, no risks)
- TASK-8902 — Loading states (dashboard, login submit, baseline save, reaction init, profile/password update); disable buttons під час submit
- TASK-8903 — Error states — замінити raw errors на читабельні Ukrainian повідомлення на key flows; production без stack traces
- TASK-8904 — Success states після зміни імені/паролю/збереження baseline/logout
- TASK-8905 — 404 page (`app/not-found.tsx`) з Ukrainian copy

### EPIC-90 Accessibility & copy pass
- TASK-9001 — Visible focus states на input/button/link
- TASK-9002 — `aria-label` на icon-only кнопках; labels на всіх input
- TASK-9003 — Контраст ≥ 4.5:1 для основного тексту (перевірити по токенах)
- TASK-9004 — Keyboard usability: всі форми проходяться Tab/Enter
- TASK-9005 — Ukrainian copy pass — кнопки/labels/errors/success/empty consistently UA; ролі: Військовий / Командир / Психолог

---

## Sprint P0-UX-3 — Regression & deploy
### EPIC-91 Regression
- TASK-9101 — Прогнати весь Playwright suite (desktop + mobile + tablet); зафіксувати green
- TASK-9102 — Backend: `pytest` (auth/RBAC/baseline/risk регрес)
- TASK-9103 — `pnpm lint` + `pnpm build` без помилок
- TASK-9104 — Manual iPhone Safari pass за demo checklist
- TASK-9105 — Manual desktop Safari + Chrome pass

### EPIC-92 Deploy
- TASK-9201 — Перевірити Railway deploy: build green, env vars cеt, домен живий
- TASK-9202 — `/api/v1/health` повертає 200; додати frontend `/health` page якщо доречно
- TASK-9203 — Demo-акаунт із multi-role перевірений (soldier + commander + psychologist)

### EPIC-93 Demo readiness
- TASK-9301 — Skript демо (`docs/03_planning/p0_ux_demo_script.md`) — 10–15 хв walkthrough
- TASK-9302 — Прогнати весь Demo readiness checklist із `lusterko_p0_ui_ux_demo_hardening.md` §17
- TASK-9303 — Опціонально: short markdown report (broken→fixed→tests added→remaining risks)

---

## Гарантії скоупу
Не входить у цей appendix (rejected у `lusterko_p0_ui_ux_demo_hardening.md` §1):
- повноцінний брендбук, складна дизайн-система, кастомні ілюстрації, складні анімації
- PDF/CSV export, email notifications, Google Analytics
- складна адмінка, нові permission-моделі, multilingual
- monitoring stack (Sentry/Grafana), feature work поза P0
