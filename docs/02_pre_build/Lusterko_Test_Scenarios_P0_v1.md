# Lusterko — Test Scenarios P0 v1

## 1. Мета P0 тестування
Перевірити, що core-контур MVP:
- працює стабільно
- не ламає role isolation
- не втрачає дані
- не залежить критично від AI
- дає пояснюваний risk output
- придатний до demo і внутрішнього тестування

## 2. Що входить у P0 test scope
### 2.1 Auth & access
- invite-based login
- Email+password flow (login, invite/accept, password reset, lockout)
- multi-role model
- role selection
- role switching
- inactive user blocking
- session validity

### 2.2 Soldier flows
- baseline onboarding
- daily check-in
- weekly reassessment
- cognitive tests
- completion summary

### 2.3 Processing layer
- AI comment parsing
- fallback при AI failure
- Risk Engine recalculation
- risk explanations

### 2.4 Role interfaces
- commander dashboard
- commander case card
- medic cases list
- medic detailed case
- medic notes/status
- admin users/roles/invites/units/audit

### 2.5 Security & audit
- server-side RBAC
- scope isolation
- audit log creation on critical actions

## 3. Що не тестуємо в P0
- advanced analytics
- reminders/notifications
- extra identity providers
- real pilot metrics
- масштабні load tests
- mobile app behavior
- deep reporting
- V2 calibration logic

## 4. Формат тест-кейсу
Кожен кейс має:
- `Test ID`
- `Title`
- `Preconditions`
- `Steps`
- `Expected result`
- `Priority`
- `Blocking?`

Пріоритети:
- `P0-critical`
- `P0-high`
- `P0-medium`

## 5. Test data set
### 5.1 Users
- `soldier_only_1`
- `commander_only_1`
- `medic_only_1`
- `admin_only_1`
- `multi_role_admin_commander`
- `multi_role_commander_medic`
- `inactive_user_1`

### 5.2 Units
- `unit_alpha`
- `unit_bravo`

### 5.3 Synthetic signal profiles
- normal / green profile
- functional yellow profile
- emotional yellow profile
- cognitive yellow profile
- cumulative red profile
- acute distress red profile
- repeated high text risk profile

## 6. Auth & access test cases

> **Sprint 7 update:** scenarios refit for email+password flow per ADR
> `docs/06_decisions/2026-05-02-auth-email-password.md`. Google OAuth path
> was removed.

### T-AUTH-001 — invite/accept creates session
Expected:
- invite consumed, password_hash set
- session created, cookie issued
- audit `invite_used` + `login_success`

### T-AUTH-002 — expired invite rejected
Expected:
- accept denied with `INVITE_EXPIRED`
- no session created

### T-AUTH-003 — invite cannot be reused
Expected:
- first accept succeeds
- second accept with same token returns `INVALID_INVITE`

### T-AUTH-004 — inactive user blocked
Expected:
- accept returns `UNAUTHORIZED`; no session

### T-AUTH-005 — single-role user auto-enters role
### T-AUTH-006 — multi-role user forced to choose role
### T-AUTH-007 — role switch updates permission context
### T-AUTH-008 — active role not assigned is rejected

### T-AUTH-009 — login with correct password
Expected:
- 200, `logged_in: true`, session cookie set
- audit `login_success`

### T-AUTH-010 — login with wrong password
Expected:
- generic `UNAUTHORIZED` (no enumeration leak)
- audit `login_failed` with `reason=UNAUTHORIZED`

### T-AUTH-011 — login locked after threshold
Expected:
- after 5 wrong attempts → `ACCOUNT_LOCKED` (HTTP 429)
- correct password during lock window also returns `ACCOUNT_LOCKED`
- audit `account_locked`
- after lock TTL passes, correct password works again

### T-AUTH-012 — successful login resets failure counter
Expected:
- 4 fails followed by a success → `auth_lockouts` row deleted
- a subsequent fail starts the count at 1, not 5

### T-AUTH-013 — exponential backoff between lock cycles
Expected:
- second lock window is 2× the first; cycle counter increments

### T-AUTH-014 — weak password rejected on invite/accept
Expected:
- `WEAK_PASSWORD` returned, no user mutation, no session
- failure does not count toward the rate-limit (UX hint, not brute-force)

### T-AUTH-015 — password forgot is anti-enumeration
Expected:
- known + unknown email both return identical envelope (`queued: true`)
- only known emails actually trigger the mailer
- repeated calls eventually trip the silent rate-limit (response shape unchanged)

### T-AUTH-016 — password reset full flow
Expected:
- reset email queued; token in URL
- POST `/auth/password/reset` with token + new password → success
- old password no longer works; new one does
- all prior sessions revoked
- audit `password_reset_requested` + `password_reset_completed`

### T-AUTH-017 — reset token cannot be reused
Expected:
- second submission with same token → `INVALID_RESET_TOKEN`

### T-AUTH-018 — expired reset token rejected
Expected:
- past `expires_at` → `RESET_TOKEN_EXPIRED`

## 7. Soldier baseline tests
### T-SOLDIER-001 — onboarding status reflects incomplete baseline
### T-SOLDIER-002 — submit baseline PHQ-4
### T-SOLDIER-003 — invalid PHQ-4 payload rejected
### T-SOLDIER-004 — baseline cannot complete if steps missing
### T-SOLDIER-005 — baseline complete unlocks daily flow

## 8. Daily check-in tests
### T-DAILY-001 — valid daily check-in submits successfully
### T-DAILY-002 — only one daily check-in per day
### T-DAILY-003 — daily blocked before baseline complete
### T-DAILY-004 — daily works without comment
### T-DAILY-005 — invalid score rejected

## 9. Weekly reassessment tests
### T-WEEKLY-001 — valid PHQ-4 weekly submission
### T-WEEKLY-002 — valid PSS-4 weekly submission
### T-WEEKLY-003 — invalid weekly payload rejected

## 10. Cognitive tests
### T-COG-001 — valid reaction test submission
### T-COG-002 — valid go/no-go submission
### T-COG-003 — invalid valid_trials rejected

## 11. AI parsing tests
### T-AI-001 — Ukrainian comment parsed successfully
### T-AI-002 — Russian comment parsed successfully
### T-AI-003 — mixed input parsed successfully
### T-AI-004 — malformed AI response does not break daily flow
### T-AI-005 — acute distress marker escalates correctly

## 12. Risk Engine tests
### T-RISK-001 — green normal case
### T-RISK-002 — yellow via functional cluster
### T-RISK-003 — yellow via weekly stress/emotional signals
### T-RISK-004 — yellow via cognitive drop
### T-RISK-005 — red via cumulative score
### T-RISK-006 — red via hard flag
### T-RISK-007 — rule hits history persisted
### T-RISK-008 — explanation text is human-readable

## 13. Commander tests
### T-CMD-001 — commander sees own unit dashboard only
### T-CMD-002 — commander cases list filters by risk
### T-CMD-003 — commander case card shows limited summary only
### T-CMD-004 — commander cannot access medic endpoint

## 14. Medic / psychologist tests
### T-MED-001 — medic sees priority cases in own unit
### T-MED-002 — medic detailed case contains needed signal layers
### T-MED-003 — medic can update case status
### T-MED-004 — medic can add note
### T-MED-005 — medic cannot access other unit cases

## 15. Admin tests
### T-ADMIN-001 — admin creates user
### T-ADMIN-002 — admin assigns multiple roles
### T-ADMIN-003 — admin generates invite
### T-ADMIN-004 — admin deactivates user
### T-ADMIN-005 — admin reactivates user
### T-ADMIN-006 — admin sees audit logs
### T-ADMIN-007 — admin cannot see medic-sensitive content by default

## 16. RBAC and leakage tests
### T-RBAC-001 — soldier cannot read another soldier data
### T-RBAC-002 — commander cannot cross unit boundary
### T-RBAC-003 — medic cannot cross unit boundary
### T-RBAC-004 — active role governs access, not total role set
### T-RBAC-005 — field-level leakage absent

## 17. Audit tests
- T-AUDIT-001 login success logged
- T-AUDIT-002 role switch logged
- T-AUDIT-003 user create/deactivate logged
- T-AUDIT-004 daily submission logged
- T-AUDIT-005 case status change logged
- T-AUDIT-006 note add logged

## 18. UX/system stability smoke tests
### T-SMOKE-001 — loading/error/success states exist on key screens
### T-SMOKE-002 — page refresh preserves valid session
### T-SMOKE-003 — logout clears access immediately

## 19. Acceptance criteria for “P0 ready”
### Auth
- valid invite login works
- expired/reused invite blocked
- multi-role selection works
- role switching works
- inactive user blocked

### Soldier flows
- baseline complete works end-to-end
- daily/weekly/cognitive submissions save correctly
- duplicate daily blocked
- completion summary works

### AI + Risk
- AI parsing works on basic uk/ru/mixed inputs
- AI failure does not break daily flow
- green/yellow/red logic works
- hard flags escalate correctly
- explanations generated

### Role interfaces
- commander sees correct scoped dashboard
- medic sees detailed scoped cases
- admin manages users/invites/roles/units/audit

### Security
- no cross-unit leaks
- no role leaks
- no sensitive field leakage
- audit trail exists for critical actions

## 20. Blocking bugs for P0
- login bypass
- reused/expired invite accepted
- inactive user can still operate
- active role ignored server-side
- cross-unit data leakage
- commander sees medic-sensitive fields
- admin sees sensitive case content by default
- second daily accepted in same day
- AI failure breaks daily submission
- Risk Engine не перераховується після relevant event
- red hard flag не ескалює
- logout не інвалідовує доступ

## 21. Мінімальний execution order тестування
### Phase 1 — Auth/security first
- AUTH
- RBAC
- session/logout
- inactive blocking

### Phase 2 — Soldier flows
- baseline
- daily
- weekly
- cognitive

### Phase 3 — Processing
- AI parse
- Risk Engine
- explanations
- case auto-open

### Phase 4 — Role UIs
- commander
- medic
- admin

### Phase 5 — Audit + smoke
- audit events
- key screens
- regression pass
