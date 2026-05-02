# Lusterko — API Contracts v1

## 1. Загальні правила API
### 1.1 Формат
- Стиль: REST
- Base path: `/api/v1`
- Формат даних: `application/json`
- Ідентифікатори: `uuid`
- Час: `ISO 8601 UTC`
- Auth: HTTP-only session cookie + refresh endpoint

### 1.2 Стандартна структура успішної відповіді
```json
{
  "success": true,
  "data": {}
}
```

### 1.3 Стандартна структура помилки
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload",
    "details": {
      "field": "sleep_score"
    }
  }
}
```

### 1.4 Стандартні error codes
- `UNAUTHORIZED`
- `FORBIDDEN`
- `INVALID_INVITE`
- `INVITE_EXPIRED`
- `INVALID_RESET_TOKEN`
- `RESET_TOKEN_EXPIRED`
- `WEAK_PASSWORD`
- `ACCOUNT_LOCKED` (HTTP 429)
- `ROLE_SELECTION_REQUIRED`
- `VALIDATION_ERROR`
- `NOT_FOUND`
- `CONFLICT`
- `DAILY_ALREADY_SUBMITTED`
- `BASELINE_NOT_COMPLETE`
- `INVALID_ACTIVE_ROLE`
- `INSUFFICIENT_SCOPE`
- `AI_PARSE_FAILED`
- `CASE_INVALID_TRANSITION`
- `INTERNAL_ERROR`

## 2. Базові enum-значення
### 2.1 Roles
```json
["soldier", "commander", "medic_psych", "admin"]
```

### 2.2 Risk status
```json
["green", "yellow", "red", "insufficient_data"]
```

### 2.3 Text risk level
```json
["none", "low", "medium", "high", "unknown"]
```

### 2.4 AI parse status
```json
["success", "failed", "partial", "skipped"]
```

### 2.5 Language detected
```json
["uk", "ru", "mixed", "unknown"]
```

### 2.6 Case review status
```json
["new", "in_review", "monitoring", "closed"]
```

### 2.7 Invite status
```json
["pending", "used", "expired", "revoked"]
```

### 2.8 User status
```json
["active", "inactive"]
```

## 3. Auth API

> **Sprint 7 Auth Pivot:** This section reflects the email+password auth (see
> `docs/06_decisions/2026-05-02-auth-email-password.md`). Google OAuth was
> removed. All auth endpoints below are rate-limited (5 failures / 15 min,
> soft-lock 5 min with exponential backoff per cycle); the lock surfaces as
> HTTP 429 + `ACCOUNT_LOCKED` (silently swallowed on `/password/forgot` to
> preserve anti-enumeration).

### 3.1 POST `/api/v1/auth/login`
**Request**
```json
{ "email": "user@example.com", "password": "..." }
```

**Response**
```json
{
  "success": true,
  "data": { "logged_in": true }
}
```

Sets the `lusterko_session` HttpOnly cookie. On wrong creds, missing user, or
inactive user returns the generic `UNAUTHORIZED` error so the API does not
leak account existence.

### 3.2 POST `/api/v1/auth/invite/accept`
**Request**
```json
{
  "token": "<plaintext-invite-token>",
  "full_name": "Ім'я Прізвище",
  "password": "..."
}
```

`full_name` is optional — when absent the admin-supplied name is kept.
On success: sets the password hash, marks the invite consumed, issues a
session cookie, returns:
```json
{ "success": true, "data": { "accepted": true } }
```

Errors: `INVALID_INVITE`, `INVITE_EXPIRED`, `WEAK_PASSWORD`, `UNAUTHORIZED`
(inactive user).

### 3.3 POST `/api/v1/auth/password/forgot`
**Request**
```json
{ "email": "user@example.com" }
```

**Response (always)**
```json
{ "success": true, "data": { "queued": true } }
```

Anti-enumeration: identical envelope regardless of whether the email matched
a real account. When the email matches an active user, the backend issues a
password-reset token and best-effort sends the reset email; failures audit
as `password_reset_email_failed` but do not surface to the caller.

### 3.4 POST `/api/v1/auth/password/reset`
**Request**
```json
{ "token": "<plaintext-reset-token>", "password": "..." }
```

On success: sets the new password hash, consumes the token, **revokes all
existing sessions for the user**, issues a fresh session cookie, returns:
```json
{ "success": true, "data": { "reset": true } }
```

Errors: `INVALID_RESET_TOKEN`, `RESET_TOKEN_EXPIRED`, `WEAK_PASSWORD`,
`UNAUTHORIZED` (inactive user).

### 3.5 GET `/api/v1/auth/me`
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "Ім'я Прізвище",
      "status": "active",
      "unit_id": "uuid"
    },
    "roles": ["soldier", "commander"],
    "active_role": "soldier",
    "role_selection_required": false
  }
}
```

### 3.6 POST `/api/v1/auth/select-role`
**Request**
```json
{ "role": "commander" }
```

**Response**
```json
{
  "success": true,
  "data": { "active_role": "commander" }
}
```

### 3.7 POST `/api/v1/auth/refresh`
```json
{
  "success": true,
  "data": { "refreshed": true }
}
```

### 3.8 POST `/api/v1/auth/logout`
```json
{
  "success": true,
  "data": { "logged_out": true }
}
```

## 4. Admin API
### 4.1 POST `/api/v1/admin/users`
**Request**
```json
{
  "full_name": "Петро Іваненко",
  "email": "petro@example.com",
  "unit_id": "uuid",
  "roles": ["soldier"]
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "full_name": "Петро Іваненко",
      "email": "petro@example.com",
      "unit_id": "uuid",
      "roles": ["soldier"],
      "status": "active"
    }
  }
}
```

### 4.2 GET `/api/v1/admin/users`
Query params:
- `unit_id`
- `status`
- `role`
- `page`
- `page_size`

### 4.3 GET `/api/v1/admin/users/{user_id}`
Повертає details користувача.

### 4.4 PATCH `/api/v1/admin/users/{user_id}`
Оновлює basic profile.

### 4.5 PUT `/api/v1/admin/users/{user_id}/roles`
**Request**
```json
{ "roles": ["soldier", "commander"] }
```

### 4.6 POST `/api/v1/admin/users/{user_id}/invite`
Повертає invite metadata і expiry.

### 4.7 POST `/api/v1/admin/users/{user_id}/deactivate`
### 4.8 POST `/api/v1/admin/users/{user_id}/reactivate`
### 4.9 GET `/api/v1/admin/units`
### 4.10 POST `/api/v1/admin/units`
### 4.11 GET `/api/v1/admin/audit-logs`

## 5. Soldier API
### 5.1 GET `/api/v1/soldier/onboarding-status`
Повертає baseline progress та next required step.

### 5.2 POST `/api/v1/soldier/baseline/phq4`
**Request**
```json
{ "answers": [1, 1, 0, 2] }
```

### 5.3 POST `/api/v1/soldier/baseline/pss4`
```json
{ "answers": [2, 1, 3, 2] }
```

### 5.4 POST `/api/v1/soldier/baseline/sleep`
```json
{ "sleep_score": 6 }
```

### 5.5 POST `/api/v1/soldier/baseline/reaction-test`
```json
{ "median_reaction_time_ms": 412, "valid_trials": 24 }
```

### 5.6 POST `/api/v1/soldier/baseline/go-no-go`
```json
{ "commission_errors": 2, "omission_errors": 1, "valid_trials": 30 }
```

### 5.7 POST `/api/v1/soldier/baseline/complete`
Повертає `baseline_completed` і `completed_at`.

### 5.8 GET `/api/v1/soldier/daily-checkins/today`
Повертає `already_submitted` і поточний day state.

### 5.9 POST `/api/v1/soldier/daily-checkins`
**Request**
```json
{
  "sleep_score": 4,
  "energy_score": 3,
  "mood_score": 5,
  "concentration_score": 4,
  "comment_text": "Погано спав, важко зосередитися"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "daily_checkin_id": "uuid",
    "risk_status": "yellow",
    "explanation_text": "Зафіксовано виражене просідання сну та енергії відносно базового профілю.",
    "ai_parse_status": "success"
  }
}
```

### 5.10 POST `/api/v1/soldier/weekly/phq4`
### 5.11 POST `/api/v1/soldier/weekly/pss4`
### 5.12 POST `/api/v1/soldier/cognitive/reaction-test`
### 5.13 POST `/api/v1/soldier/cognitive/go-no-go`
### 5.14 GET `/api/v1/soldier/completion-summary`
Повертає `daily_due`, `weekly_due`, `cognitive_due`, `last_risk_status`.

## 6. Commander API
### 6.1 GET `/api/v1/commander/dashboard/summary`
Повертає counts по status для own unit.

### 6.2 GET `/api/v1/commander/dashboard/cases`
Повертає cases list з filters.

### 6.3 GET `/api/v1/commander/cases/{user_id}`
Повертає basic case card без чутливої клінічної деталізації.

## 7. Medic / Psychologist API
### 7.1 GET `/api/v1/medic/cases`
### 7.2 GET `/api/v1/medic/cases/{case_review_id}`
### 7.3 PATCH `/api/v1/medic/cases/{case_review_id}`
### 7.4 POST `/api/v1/medic/cases/{case_review_id}/notes`

## 8. Internal AI API
### 8.1 POST `/internal/ai/analyze-comment`
**Request**
```json
{ "text": "Погано спав, тривожно, важко зосередитися" }
```

**Response**
```json
{
  "language_detected": "uk",
  "has_signal": true,
  "markers": ["sleep_issue", "anxiety_tension", "concentration_problem"],
  "text_risk_level": "medium",
  "confidence_score": 0.88,
  "summary_for_system": "Виявлено ознаки порушення сну, тривоги та зниження концентрації.",
  "parse_status": "success"
}
```

## 9. Role-based field policy
### Soldier бачить
- власний completion state
- факт відправки
- поточний status
- коротке explanation
- без сирого AI JSON

### Commander бачить
- summary status
- explanation text
- агреговану динаміку
- без note history медика
- без повної деталізації psychometrics

### Medic / psychologist бачить
- детальні сигнали
- AI markers
- summary_for_system
- case notes
- risk score/explanation

### Admin бачить
- users / roles / units / invites / audit
- без автоматичного доступу до всього чутливого case content

## 10. Acceptance rules для API
- inactive user не може увійти
- invite не може бути використаний двічі
- роль не можна обрати поза своїм assigned set
- не більше 1 daily check-in на день
- без completed baseline — `BASELINE_NOT_COMPLETE`
- commander/medic працюють лише в межах свого unit
- soldier бачить лише себе
- якщо AI parser впав, daily все одно зберігається

## 11. Що ще треба в API v1.1
- OpenAPI spec / Swagger schema
- pagination standard everywhere
- sort parameters
- filter grammar
- idempotency rules
- rate limits
- exact auth-cookie policy
- versioning policy
