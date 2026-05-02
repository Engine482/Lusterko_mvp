# Lusterko — Development Backlog v1

## Sprint 0 — Repo + Infra + Foundations
### EPIC-00 Repo bootstrap
- TASK-0001 — Створити repo structure
- TASK-0002 — Зафіксувати tech stack

### EPIC-01 Backend skeleton
- TASK-0101 — Підняти базовий FastAPI app
- TASK-0102 — Створити модульну структуру backend
- TASK-0103 — Налаштувати config layer

### EPIC-02 Database foundation
- TASK-0201 — Підняти PostgreSQL для local dev
- TASK-0202 — Підключити SQLAlchemy + Alembic
- TASK-0203 — Реалізувати initial schema migration

### EPIC-03 Frontend skeleton
- TASK-0301 — Підняти Next.js app
- TASK-0302 — Створити frontend route structure
- TASK-0303 — Створити shared UI shell

### EPIC-04 Shared types & constants
- TASK-0401 — Винести shared enums
- TASK-0402 — Створити base API response schemas

### EPIC-05 Dev tooling
- TASK-0501 — Налаштувати lint/format
- TASK-0502 — Налаштувати minimal CI

### EPIC-06 Seed/test foundation
- TASK-0601 — Написати seed script
- TASK-0602 — Створити test fixtures scaffold

## Sprint 1 — Auth + Access + Admin Basic
### EPIC-10 Auth core
- TASK-1001 — Реалізувати invite validation service
- TASK-1002 — Реалізувати `GET /api/v1/auth/google/start`
- TASK-1003 — Інтегрувати Google OAuth callback
- TASK-1004 — Реалізувати session creation
- TASK-1005 — Реалізувати `GET /api/v1/auth/me`
- TASK-1006 — Реалізувати `POST /api/v1/auth/select-role`
- TASK-1007 — Реалізувати `POST /api/v1/auth/refresh`
- TASK-1008 — Реалізувати `POST /api/v1/auth/logout`

### EPIC-11 RBAC foundation
- TASK-1101 — Реалізувати `require_authenticated_session`
- TASK-1102 — Реалізувати `require_active_role`
- TASK-1103 — Реалізувати `require_scope`
- TASK-1104 — Реалізувати role switch audit logging

### EPIC-12 Admin basic
- TASK-1201 — Реалізувати `POST /api/v1/admin/users`
- TASK-1202 — Реалізувати `GET /api/v1/admin/users`
- TASK-1203 — Реалізувати `GET /api/v1/admin/users/{id}`
- TASK-1204 — Реалізувати `PATCH /api/v1/admin/users/{id}`
- TASK-1205 — Реалізувати `PUT /api/v1/admin/users/{id}/roles`
- TASK-1206 — Реалізувати `POST /api/v1/admin/users/{id}/invite`
- TASK-1207 — Реалізувати deactivate/reactivate
- TASK-1208 — Реалізувати units endpoints

### EPIC-13 Audit basic
- TASK-1301 — Реалізувати audit write helper
- TASK-1302 — Логувати critical auth events
- TASK-1303 — Логувати critical admin events

### EPIC-14 Frontend auth/admin
- TASK-1401 — Зібрати Invite Landing Screen
- TASK-1402 — Зібрати OAuth transition screen
- TASK-1403 — Зібрати Role Selection Screen
- TASK-1404 — Зібрати Global Role Switcher
- TASK-1405 — Зібрати Admin Dashboard
- TASK-1406 — Зібрати Users List
- TASK-1407 — Зібрати Create User screen
- TASK-1408 — Зібрати User Profile screen
- TASK-1409 — Зібрати Units screen

### EPIC-15 Tests for Sprint 1
- TASK-1501 — Покрити auth integration tests
- TASK-1502 — Покрити admin integration tests
- TASK-1503 — Покрити RBAC tests Sprint 1
- TASK-1504 — Smoke check frontend auth/admin

## Sprint 2 — Soldier Baseline + Daily
### EPIC-20 Soldier domain models & schema
- TASK-2001 — Додати міграцію для `baseline_profiles`
- TASK-2002 — Додати міграцію для `baseline_events`
- TASK-2003 — Додати міграцію для `daily_checkins`
- TASK-2004 — Додати ORM models для baseline/daily

### EPIC-21 Soldier backend services
- TASK-2101 — Реалізувати onboarding status service
- TASK-2102 — Реалізувати baseline PHQ-4 service
- TASK-2103 — Реалізувати baseline PSS-4 service
- TASK-2104 — Реалізувати baseline sleep service
- TASK-2105 — Реалізувати baseline reaction test service
- TASK-2106 — Реалізувати baseline go/no-go service
- TASK-2107 — Реалізувати baseline completion service
- TASK-2108 — Реалізувати daily check-in service
- TASK-2109 — Реалізувати completion summary service

### EPIC-22 Soldier API
- TASK-2201 — `GET /api/v1/soldier/onboarding-status`
- TASK-2202 — `POST /api/v1/soldier/baseline/phq4`
- TASK-2203 — `POST /api/v1/soldier/baseline/pss4`
- TASK-2204 — `POST /api/v1/soldier/baseline/sleep`
- TASK-2205 — `POST /api/v1/soldier/baseline/reaction-test`
- TASK-2206 — `POST /api/v1/soldier/baseline/go-no-go`
- TASK-2207 — `POST /api/v1/soldier/baseline/complete`
- TASK-2208 — `GET /api/v1/soldier/daily-checkins/today`
- TASK-2209 — `POST /api/v1/soldier/daily-checkins`
- TASK-2210 — `GET /api/v1/soldier/completion-summary`

### EPIC-23 Soldier frontend shell
- TASK-2301 — Створити soldier route group/layout
- TASK-2302 — Зібрати Soldier Home screen
- TASK-2303 — Зібрати baseline progress shell

### EPIC-24 Baseline frontend screens
- TASK-2401 — PHQ-4 screen
- TASK-2402 — PSS-4 screen
- TASK-2403 — Sleep screen
- TASK-2404 — Reaction Test screen
- TASK-2405 — Go / No-Go screen
- TASK-2406 — Baseline Completion screen

### EPIC-25 Daily frontend screens
- TASK-2501 — Daily Check-in screen
- TASK-2502 — Daily Success screen
- TASK-2503 — State “already submitted today”
- TASK-2504 — Інтеграція Home ↔ Daily flow

### EPIC-26 Due-state logic v0
- TASK-2601 — Реалізувати soldier due-state calculator
- TASK-2602 — Реалізувати label set

### EPIC-27 RBAC / security for soldier flows
- TASK-2701 — Заборонити доступ не-soldier active role
- TASK-2702 — Заборонити доступ soldier до чужих даних
- TASK-2703 — Перевірити field filtering на soldier responses

### EPIC-28 Audit for soldier flows
- TASK-2801 — Логувати baseline step submissions
- TASK-2802 — Логувати baseline completion
- TASK-2803 — Логувати daily submission

### EPIC-29 Tests for Sprint 2
- TASK-2901 — Onboarding status tests
- TASK-2902 — Baseline submission tests
- TASK-2903 — Baseline completion gate tests
- TASK-2904 — Daily submission tests
- TASK-2905 — RBAC tests for soldier endpoints
- TASK-2906 — Frontend smoke tests for soldier flow

## Sprint 3 — Weekly + Cognitive + AI Parsing
### EPIC-30 Weekly & cognitive schema
- TASK-3001 — `weekly_phq4_assessments`
- TASK-3002 — `weekly_pss4_assessments`
- TASK-3003 — `reaction_tests`
- TASK-3004 — `go_no_go_tests`
- TASK-3005 — `comment_ai_analyses`
- TASK-3006 — ORM models for weekly/cognitive/AI tables

### EPIC-31 Weekly backend services
- TASK-3101 — weekly PHQ-4 service
- TASK-3102 — weekly PSS-4 service
- TASK-3103 — weekly due-state hooks

### EPIC-32 Cognitive backend services
- TASK-3201 — periodic reaction test service
- TASK-3202 — periodic go/no-go service
- TASK-3203 — cognitive due-state hooks

### EPIC-33 AI parsing service
- TASK-3301 — AI service wrapper
- TASK-3302 — system prompt for comment parsing
- TASK-3303 — few-shot examples
- TASK-3304 — JSON parse/validation layer
- TASK-3305 — language detection normalization
- TASK-3306 — marker normalization
- TASK-3307 — `text_risk_level` normalization
- TASK-3308 — fallback policy
- TASK-3309 — persistence in `comment_ai_analyses`

### EPIC-34 Internal AI API
- TASK-3401 — `POST /internal/ai/analyze-comment`
- TASK-3402 — internal-only protection

### EPIC-35 Soldier API expansion
- TASK-3501 — weekly PHQ-4 endpoint
- TASK-3502 — weekly PSS-4 endpoint
- TASK-3503 — cognitive reaction endpoint
- TASK-3504 — cognitive go/no-go endpoint
- TASK-3505 — update completion summary
- TASK-3506 — daily submission + AI parsing integration

### EPIC-36 Weekly & cognitive frontend
- TASK-3601 — Weekly Reassessment flow
- TASK-3602 — Cognitive Task Launcher
- TASK-3603 — periodic Reaction Test screen
- TASK-3604 — periodic Go / No-Go screen
- TASK-3605 — інтеграція з Soldier Home

### EPIC-37 Soldier Home / due-state expansion
- TASK-3701 — weekly/cognitive due states
- TASK-3702 — labels/status cards update

### EPIC-38 RBAC / security hardening for Sprint 3
- TASK-3801 — deny wrong active roles
- TASK-3802 — internal AI endpoint not public
- TASK-3803 — soldier field filtering after AI integration

### EPIC-39 Audit for Sprint 3
- TASK-3901 — log weekly submissions
- TASK-3902 — log cognitive submissions
- TASK-3903 — log AI parsing result events

### EPIC-40 Tests for Sprint 3
- TASK-4001 — weekly endpoint tests
- TASK-4002 — cognitive endpoint tests
- TASK-4003 — AI parser wrapper tests
- TASK-4004 — daily + AI fallback tests
- TASK-4005 — RBAC tests for Sprint 3
- TASK-4006 — Frontend smoke tests for weekly/cognitive flows

## Sprint 4 — Risk Engine + Commander
### EPIC-40 Risk schema
- TASK-4001 — `risk_statuses`
- TASK-4002 — `risk_events`
- TASK-4003 — `risk_rule_hits`
- TASK-4004 — ORM models for risk tables

### EPIC-41 Risk Engine core service
- TASK-4101 — domain scoring orchestrator
- TASK-4102 — functional scoring rules
- TASK-4103 — emotional/stress scoring rules
- TASK-4104 — cognitive scoring rules
- TASK-4105 — text modifier rules
- TASK-4106 — final aggregation
- TASK-4107 — insufficient_data logic
- TASK-4108 — explanation builder

### EPIC-42 Risk persistence & triggers
- TASK-4201 — recompute after daily
- TASK-4202 — recompute after weekly PHQ-4
- TASK-4203 — recompute after weekly PSS-4
- TASK-4204 — recompute after reaction test
- TASK-4205 — recompute after go/no-go
- TASK-4206 — recompute after baseline completion
- TASK-4207 — upsert/update `risk_statuses`
- TASK-4208 — insert `risk_events`
- TASK-4209 — insert `risk_rule_hits`

### EPIC-43 Commander backend
- TASK-4301 — summary query for dashboard
- TASK-4302 — cases list query
- TASK-4303 — commander case card query
- TASK-4304 — unit-scope enforcement

### EPIC-44 Commander API
- TASK-4401 — dashboard/summary
- TASK-4402 — dashboard/cases
- TASK-4403 — commander/cases/{user_id}

### EPIC-45 Commander frontend
- TASK-4501 — Commander Dashboard
- TASK-4502 — Commander Cases List
- TASK-4503 — Commander Case Card
- TASK-4504 — integration Dashboard ↔ Cases ↔ Case Card

### EPIC-46 Field filtering & privacy hardening
- TASK-4601 — commander response serializer/filtering
- TASK-4602 — soldier response compatibility after Risk Engine
- TASK-4603 — groundwork for medic-visible fields

### EPIC-47 Audit for Sprint 4
- TASK-4701 — log risk recomputation events
- TASK-4702 — log commander access to case card
- TASK-4703 — log denied cross-unit access attempts

### EPIC-48 Tests for Sprint 4
- TASK-4801 — functional domain tests
- TASK-4802 — emotional/stress tests
- TASK-4803 — cognitive tests
- TASK-4804 — text modifier tests
- TASK-4805 — final aggregation tests
- TASK-4806 — persistence tests
- TASK-4807 — commander endpoint tests
- TASK-4808 — RBAC/field leakage tests
- TASK-4809 — frontend smoke tests: commander flow

## Sprint 5 — Medic + Case Review + Audit + Stabilization
### EPIC-50 Case review schema
- TASK-5001 — `case_reviews`
- TASK-5002 — `case_review_notes`
- TASK-5003 — ORM models for case review tables

### EPIC-51 Case auto-open and lifecycle
- TASK-5101 — auto-open logic for red cases
- TASK-5102 — auto-open logic for persistent yellow
- TASK-5103 — case priority update on repeated risk events
- TASK-5104 — case status transition rules

### EPIC-52 Medic backend queries/services
- TASK-5201 — medic priority cases query
- TASK-5202 — medic detailed case query
- TASK-5203 — add case note service
- TASK-5204 — update case status service
- TASK-5205 — medic unit-scope enforcement

### EPIC-53 Medic API
- TASK-5301 — GET /medic/cases
- TASK-5302 — GET /medic/cases/{case_review_id}
- TASK-5303 — PATCH /medic/cases/{case_review_id}
- TASK-5304 — POST /medic/cases/{case_review_id}/notes

### EPIC-54 Medic frontend
- TASK-5401 — Medic Priority Cases List
- TASK-5402 — Medic Detailed Case View
- TASK-5403 — Update Case Status block
- TASK-5404 — Add Note block
- TASK-5405 — інтеграція Medic List ↔ Detailed Case View

### EPIC-55 Admin audit UI
- TASK-5501 — GET /admin/audit-logs
- TASK-5502 — Audit Log Screen
- TASK-5503 — basic audit filters

### EPIC-56 Final privacy / RBAC hardening
- TASK-5601 — admin не бачить medic-sensitive payload by default
- TASK-5602 — commander не бачить medic notes
- TASK-5603 — soldier не бачить internal risk internals
- TASK-5604 — backend-side field filtering final pass
- TASK-5605 — log denied sensitive access attempts

### EPIC-57 Audit coverage finalization
- TASK-5701 — log case opened events
- TASK-5702 — log case status changed events
- TASK-5703 — log case note added events
- TASK-5704 — log commander case access events
- TASK-5705 — log medic case access events
- TASK-5706 — log denied access events

### EPIC-58 Stabilization & regression
- TASK-5801 — full P0-critical regression pass
- TASK-5802 — full end-to-end smoke script
- TASK-5803 — loading/error/empty state review
- TASK-5804 — duplicate / race condition edge cases
- TASK-5805 — demo seed data

### EPIC-59 Tests for Sprint 5
- TASK-5901 — case auto-open logic tests
- TASK-5902 — medic endpoint tests
- TASK-5903 — audit logs endpoint tests
- TASK-5904 — RBAC leakage tests final
- TASK-5905 — frontend smoke tests: medic flow
- TASK-5906 — frontend smoke tests: audit screen

## Sprint 6 — Deployment, Email Delivery, Pilot Bootstrap
### EPIC-60 Production runtime (Docker)
- TASK-6001 — Backend Dockerfile (multi-stage uv build → slim runtime)
- TASK-6002 — Frontend Dockerfile (multi-stage `next build` → `next start`)
- TASK-6003 — `infra/docker-compose.prod.yml` (backend + frontend + postgres-prod)
- TASK-6004 — Окремий `lusterko-postgres-prod` контейнер з ізольованим volume і паролем (не `change_me`)
- TASK-6005 — `.env.production.example` з переліком всіх обов'язкових prod-змінних

### EPIC-61 Domain & TLS (lusterko.motornyi.com)
- TASK-6101 — DNS A-запис `lusterko.motornyi.com` → IP сервера (виконує власник домену)
- TASK-6102 — Nginx reverse proxy vhost у `infra/nginx/lusterko.conf` (`/` → frontend:3000, `/api/` → backend:8000)
- TASK-6103 — Let's Encrypt cert через certbot + systemd timer renewal
- TASK-6104 — Перевірити що `APP_ENV=production` дійсно вмикає `secure=True` для session cookie

### EPIC-62 Deploy automation & ops
- TASK-6201 — `scripts/deploy.sh` (git pull → docker compose build → alembic upgrade → recreate containers, без даунтайму postgres)
- TASK-6202 — `scripts/backup_db.sh` + cron приклад (щоденний `pg_dump` prod БД у `/var/backups/lusterko`)
- TASK-6203 — Healthchecks у `docker-compose.prod.yml` для backend (`/api/v1/health`), frontend, postgres
- TASK-6204 — Structured logging у backend (JSON формат, читається `docker logs`)

### EPIC-63 Config cleanup before pilot
- TASK-6301 — Видалити `SESSION_SECRET` з `app/core/config.py` і env-шаблонів (мертвий конфіг — не використовується)
- TASK-6302 — Узгодити frontend prod port: `next start -p 3000` для prod, dev лишається 3001
- TASK-6303 — Завести реальний Google OAuth client для пілоту (production credentials), не stub
- TASK-6304 — Guard у `seed_demo.py` — відмова при `APP_ENV=production` без явного `FORCE=1`

### EPIC-64 Invite email delivery
- TASK-6401 — Mailer service `app/modules/notifications/mailer.py` зі стратегіями `StubMailer` (dev) + `SmtpMailer` (prod), як AI parser pattern
- TASK-6402 — Шаблон листа "Запрошення до Lusterko" українською (plaintext + minimal HTML) з повним інвайт-URL
- TASK-6403 — Виклик mailer з `POST /api/v1/admin/users/{id}/invite` — best-effort, не блокує відповідь, помилка логується
- TASK-6404 — Аудит-події `invite_email_sent` / `invite_email_failed`
- TASK-6405 — env vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `INVITE_FROM_EMAIL`, `APP_PUBLIC_BASE_URL`
- TASK-6406 — Тести: stub mailer фіксує invite_url; SMTP-помилка не валить запит на створення інвайта

### EPIC-65 Pilot bootstrap
- TASK-6501 — Розширити `scripts/seed.py` параметром `BOOTSTRAP_USER_ROLES` (CSV) для multi-role admin
- TASK-6502 — Виконати seed на prod БД: `ADMIN_EMAIL=motorny.v@gmail.com`, ролі `admin,soldier,commander,medic`, unit "Тестовий підрозділ"
- TASK-6503 — Smoke перевірка: інвайт-лист реально дійшов на motorny.v@gmail.com → перший вхід → перемикання між усіма ролями

### EPIC-66 Stabilization for pilot
- TASK-6601 — CI крок: `docker compose -f infra/docker-compose.prod.yml build` (проста перевірка що Dockerfile-и не ламаються)
- TASK-6602 — End-to-end smoke на pilot БД: invite → login → daily → weekly → cognitive → commander dashboard → medic case → close
- TASK-6603 — README розділ "Production deployment" з покроковою інструкцією (DNS, certbot, env, deploy.sh)

## Sprint 7 — Auth Pivot (Google OAuth → email+password)

> **Decision:** повний rationale у `docs/06_decisions/2026-05-02-auth-email-password.md`.
> Параметри: argon2id (12-char min), rate-limit `/login` 5/15хв на пару (IP,email)
> + soft-lock 5хв, токени invite 7д / reset 1г, session 30д rolling. Без 2FA на P0.
> SSO/SAML відкладено до V1.

### EPIC-70 Backend auth (Google → email+password)
- TASK-7001 — Alembic міграція: `users.password_hash`, таблиця `password_reset_tokens (id, user_id, token_hash, expires_at, consumed_at)`
- TASK-7002 — `app/core/security/passwords.py`: argon2id hash/verify, мінімум 12 символів, опціонально top-N block-list
- TASK-7003 — `POST /api/v1/auth/login` — email+password → session cookie
- TASK-7004 — `POST /api/v1/auth/logout` — clear session
- TASK-7005 — `POST /api/v1/auth/invite/accept` — invite_token + full_name + password → user + session
- TASK-7006 — `POST /api/v1/auth/password/forgot` — anti-enumeration; reset email
- TASK-7007 — `POST /api/v1/auth/password/reset` — reset_token + password → update + session
- TASK-7008 — Видалити `app/modules/auth/google.py`, `user_identities`, `GOOGLE_CLIENT_*` env, dev-stub flow
- TASK-7009 — Видалити Google-related тести; конфіг очистити

### EPIC-71 Mailer extension
- TASK-7101 — `send_password_reset(...)` у `app/modules/notifications/mailer.py`
- TASK-7102 — UA шаблон листа "Скидання паролю в Lusterko" (plaintext+HTML)
- TASK-7103 — Аудит-події `password_reset_requested`, `password_reset_completed`

### EPIC-72 Brute-force захист
- TASK-7201 — Rate-limit (5/15хв per IP+email) на `/login`, `/password/forgot`, `/password/reset`, `/invite/accept`
- TASK-7202 — Soft-lockout: 5 fail-у-рядок → 5хв lock; експоненційний backoff кожного наступного циклу
- TASK-7203 — Аудит-події `login_failed`, `account_locked`

### EPIC-73 Frontend
- TASK-7301 — `/login` (email + password + "Забули пароль?")
- TASK-7302 — `/invite?token=XXX` (set initial password)
- TASK-7303 — `/forgot-password` (email form, генерична відповідь)
- TASK-7304 — `/reset-password?token=XXX` (новий пароль + confirm)
- TASK-7305 — Видалити Google-OAuth екрани і callback handler

### EPIC-74 Bootstrap & docs
- TASK-7401 — `scripts/seed.py`: підтримка `BOOTSTRAP_ADMIN_PASSWORD` (argon2id, idempotent)
- TASK-7402 — `docs/01_product/PRD.md` — замінити всі згадки Google OAuth на email+password; додати посилання на ADR
- TASK-7403 — `docs/02_pre_build/Lusterko_API_Contracts_v1.md` — нові auth endpoints, видалити Google-related
- TASK-7404 — `docs/02_pre_build/Lusterko_DB_Schema_v1.md` — `password_hash`, `password_reset_tokens`; видалити `user_identities`
- TASK-7405 — `docs/02_pre_build/Lusterko_Test_Scenarios_P0_v1.md` — auth scenarios оновити
- TASK-7406 — `docs/02_pre_build/Lusterko_Wireframes_P0_v1.md` — login/invite/forgot/reset екрани
- TASK-7407 — README + AGENTS.md, де згадка Google OAuth — оновити

### EPIC-75 Tests
- TASK-7501 — argon2id hash/verify; length policy enforcement
- TASK-7502 — invite/accept: happy + used-token + expired-token
- TASK-7503 — login: success / wrong-password / locked / rate-limited
- TASK-7504 — forgot/reset full flow + reuse + expired
- TASK-7505 — RBAC end-to-end smoke (інваріант: ролі не змінились після auth swap)
