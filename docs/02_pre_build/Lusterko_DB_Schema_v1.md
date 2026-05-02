# Lusterko — DB Schema v1

## 1. Загальні принципи
- СУБД: PostgreSQL
- Primary keys: UUID
- timestamps: `timestamptz`
- soft delete: вибірково
- деактивація користувача через `status`, а не delete
- naming: `snake_case`
- для MVP: constrained text + check constraints замість важких enum-type міграцій

## 2. Організаційний контур
### 2.1 `units`
- `id uuid pk`
- `name text not null`
- `code text null`
- `is_active boolean not null default true`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Constraints:
- unique (`name`)

### 2.2 `users`
- `id uuid pk`
- `full_name text not null`
- `email text not null`
- `unit_id uuid null references units(id)`
- `status text not null default 'active'`
- `password_hash text null` — argon2id PHC string; NULL means the user has not yet accepted their invite or finished a password reset (login rejects such rows)
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Allowed status:
- `active`
- `inactive`

Constraints:
- unique (`email`)
- check `status in ('active', 'inactive')`

### 2.3 `user_roles`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `role text not null`
- `created_at timestamptz not null default now()`

Allowed role:
- `soldier`
- `commander`
- `medic_psych`
- `admin`

Constraints:
- unique (`user_id`, `role`)
- check `role in ('soldier', 'commander', 'medic_psych', 'admin')`

### 2.4 `password_reset_tokens`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `token_hash text not null` — sha-256 of the plaintext token (the plaintext is only ever in the email)
- `expires_at timestamptz not null` — typically 1 hour after issuance (see `PASSWORD_RESET_TTL`)
- `consumed_at timestamptz null` — set when the user submits a successful reset
- `created_at timestamptz not null default now()`

Constraints:
- unique (`token_hash`)
- index (`user_id`)

> Sprint 7 replaced the prior `user_identities` table (Google OAuth subject mapping) with this table. See `docs/06_decisions/2026-05-02-auth-email-password.md` for rationale.

### 2.5 `auth_invites`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `token_hash text not null`
- `status text not null default 'pending'`
- `expires_at timestamptz not null`
- `used_at timestamptz null`
- `revoked_at timestamptz null`
- `created_by_user_id uuid null references users(id)`
- `created_at timestamptz not null default now()`

Allowed status:
- `pending`
- `used`
- `expired`
- `revoked`

Constraints:
- unique (`token_hash`)
- check `status in ('pending', 'used', 'expired', 'revoked')`

### 2.6 `user_sessions`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `active_role text not null`
- `status text not null default 'active'`
- `refresh_token_hash text null`
- `ip_address inet null`
- `user_agent text null`
- `expires_at timestamptz not null`
- `last_seen_at timestamptz not null default now()`
- `created_at timestamptz not null default now()`

Allowed active_role:
- `soldier`
- `commander`
- `medic_psych`
- `admin`

Allowed status:
- `active`
- `revoked`
- `expired`

### 2.7 `auth_lockouts`
- `id uuid pk`
- `key text not null` — composite key encoding endpoint + (IP, email) coordinate, e.g. `login:1.2.3.4:user@example.com`
- `failed_count integer not null default 0`
- `cycle integer not null default 0` — exponential-backoff cycle index (0 → BASE, 1 → 2× BASE, ...)
- `locked_until timestamptz null`
- `last_failure_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Constraints:
- unique (`key`)
- index (`key`), index (`locked_until`)

> Brute-force protection state for `/auth/login`, `/auth/invite/accept`, `/auth/password/forgot`, `/auth/password/reset`. Threshold 5 failures / 15-min sliding window; lock 5 min on first cycle, exponential backoff capped at 24 h. Successful auth deletes the row.

## 3. Baseline та оцінки
### 3.1 `baseline_profiles`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `baseline_sleep_score integer null`
- `baseline_energy_score integer null`
- `baseline_mood_score integer null`
- `baseline_concentration_score integer null`
- `baseline_phq4_total integer null`
- `baseline_pss4_total integer null`
- `baseline_reaction_time_median_ms integer null`
- `baseline_go_no_go_commission_errors integer null`
- `baseline_go_no_go_omission_errors integer null`
- `baseline_completed boolean not null default false`
- `completed_at timestamptz null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

### 3.2 `baseline_events`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `step_code text not null`
- `payload_json jsonb not null`
- `recorded_at timestamptz not null default now()`
- `created_at timestamptz not null default now()`

Allowed `step_code`:
- `phq4`
- `pss4`
- `sleep`
- `reaction_test`
- `go_no_go`

### 3.3 `daily_checkins`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `checkin_date date not null`
- `sleep_score integer not null`
- `energy_score integer not null`
- `mood_score integer not null`
- `concentration_score integer not null`
- `comment_text text null`
- `created_at timestamptz not null default now()`

Constraints:
- unique (`user_id`, `checkin_date`)
- all scores `between 0 and 10`
- `comment_text <= 300 chars`

### 3.4 `weekly_phq4_assessments`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `assessment_date date not null`
- `answer_1 integer not null`
- `answer_2 integer not null`
- `answer_3 integer not null`
- `answer_4 integer not null`
- `total_score integer not null`
- `created_at timestamptz not null default now()`

### 3.5 `weekly_pss4_assessments`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `assessment_date date not null`
- `answer_1 integer not null`
- `answer_2 integer not null`
- `answer_3 integer not null`
- `answer_4 integer not null`
- `total_score integer not null`
- `created_at timestamptz not null default now()`

### 3.6 `reaction_tests`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `test_date date not null`
- `context text not null`
- `median_reaction_time_ms integer not null`
- `valid_trials integer not null`
- `created_at timestamptz not null default now()`

Allowed context:
- `baseline`
- `cognitive`

### 3.7 `go_no_go_tests`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `test_date date not null`
- `context text not null`
- `commission_errors integer not null`
- `omission_errors integer not null`
- `valid_trials integer not null`
- `created_at timestamptz not null default now()`

## 4. AI-аналіз
### 4.1 `comment_ai_analyses`
- `id uuid pk`
- `daily_checkin_id uuid not null references daily_checkins(id) on delete cascade`
- `language_detected text not null`
- `has_signal boolean not null default false`
- `markers jsonb not null default '[]'::jsonb`
- `text_risk_level text not null`
- `confidence_score numeric(4,3) not null default 0`
- `summary_for_system text null`
- `parse_status text not null`
- `raw_model_name text null`
- `created_at timestamptz not null default now()`

Allowed language_detected:
- `uk`
- `ru`
- `mixed`
- `unknown`

Allowed text_risk_level:
- `none`
- `low`
- `medium`
- `high`
- `unknown`

Allowed parse_status:
- `success`
- `failed`
- `partial`
- `skipped`

## 5. Risk Engine
### 5.1 `risk_statuses`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `current_risk_status text not null`
- `current_risk_score numeric(4,1) not null default 0`
- `functional_score numeric(4,1) not null default 0`
- `emotional_score numeric(4,1) not null default 0`
- `cognitive_score numeric(4,1) not null default 0`
- `text_modifier_score numeric(4,1) not null default 0`
- `hard_flag text null`
- `explanation_text text null`
- `calculated_at timestamptz not null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

### 5.2 `risk_events`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `source_event_type text not null`
- `source_event_id uuid not null`
- `previous_status text null`
- `new_status text not null`
- `total_score numeric(4,1) not null`
- `hard_flag text null`
- `explanation_text text null`
- `created_at timestamptz not null default now()`

### 5.3 `risk_rule_hits`
- `id uuid pk`
- `risk_event_id uuid not null references risk_events(id) on delete cascade`
- `rule_code text not null`
- `domain text not null`
- `weight numeric(4,1) not null`
- `details_json jsonb not null default '{}'::jsonb`
- `created_at timestamptz not null default now()`

## 6. Case management
### 6.1 `case_reviews`
- `id uuid pk`
- `user_id uuid not null references users(id) on delete cascade`
- `status text not null default 'new'`
- `opened_at timestamptz not null default now()`
- `closed_at timestamptz null`
- `last_risk_event_id uuid null references risk_events(id)`
- `assigned_to_user_id uuid null references users(id)`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Status:
- `new`
- `in_review`
- `monitoring`
- `closed`

Потрібен partial unique index на один незакритий кейс на user.

### 6.2 `case_review_notes`
- `id uuid pk`
- `case_review_id uuid not null references case_reviews(id) on delete cascade`
- `author_user_id uuid not null references users(id)`
- `text text not null`
- `created_at timestamptz not null default now()`

## 7. Audit
### 7.1 `audit_logs`
- `id uuid pk`
- `actor_user_id uuid null references users(id)`
- `target_user_id uuid null references users(id)`
- `event_type text not null`
- `entity_type text null`
- `entity_id uuid null`
- `metadata_json jsonb not null default '{}'::jsonb`
- `ip_address inet null`
- `created_at timestamptz not null default now()`

Suggested event types:
- `login_success`
- `login_failed`
- `logout`
- `role_selected`
- `role_switched`
- `user_created`
- `user_updated`
- `user_deactivated`
- `user_reactivated`
- `invite_created`
- `invite_used`
- `invite_email_sent`
- `invite_email_failed`
- `password_reset_requested`
- `password_reset_completed`
- `password_reset_email_sent`
- `password_reset_email_failed`
- `account_locked`
- `daily_checkin_submitted`
- `weekly_phq4_submitted`
- `weekly_pss4_submitted`
- `reaction_test_submitted`
- `go_no_go_submitted`
- `case_opened`
- `case_status_changed`
- `case_note_added`

## 8. Індекси
### users
- index on `unit_id`
- index on `status`

### user_roles
- index on `user_id`
- index on `role`

### auth_invites
- index on `user_id`
- index on `status`
- index on `expires_at`

### password_reset_tokens
- index on `user_id`
- unique on `token_hash`

### auth_lockouts
- unique on `key`
- index on `key`
- index on `locked_until`

### user_sessions
- index on `user_id`
- index on `status`
- index on `expires_at`

### daily_checkins
- unique on (`user_id`, `checkin_date`)
- index on (`user_id`, `checkin_date desc`)

### weekly / cognitive
- index on recent user assessments

### comment_ai_analyses
- unique on `daily_checkin_id`
- index on `text_risk_level`

### risk_statuses
- unique on `user_id`
- index on `current_risk_status`

### risk_events
- index on (`user_id`, `created_at desc`)
- index on (`new_status`, `created_at desc`)

### case_reviews
- index on `user_id`
- index on `status`
- index on `assigned_to_user_id`

### audit_logs
- index on `actor_user_id`
- index on `target_user_id`
- index on `created_at desc`
- index on `event_type`

## 9. Мінімальні зв’язки по потоках
### Soldier daily flow
`users` → `daily_checkins` → `comment_ai_analyses` → `risk_events` → `risk_rule_hits` → update `risk_statuses`

### Weekly / cognitive
`users` → assessments/tests → `risk_events` → `risk_rule_hits` → update `risk_statuses`

### Medic workflow
`risk_events` + `risk_statuses` → `case_reviews` → `case_review_notes`

### Admin workflow
`users`, `user_roles`, `auth_invites`, `units`, `audit_logs`

## 10. Що не ускладнювати в P0
- окремі таблиці під кожен AI marker
- event sourcing архітектуру
- складні permission tables
- soft delete всюди
- multi-tenant design
- мікросервісний поділ

## 11. Що ще треба після DB Schema
- `RBAC Matrix v1`
- `Test Scenarios P0`
