# Lusterko — RBAC Matrix v1

## 1. Принцип моделі доступу
Доступ визначається зв’язкою:

`authenticated user + active session + active role + scope`

Тобто:
- бути залогіненим недостатньо;
- мати роль недостатньо;
- активна роль у сесії обов’язкова;
- scope до unit / self / case теж обов’язковий;
- усі перевірки — на сервері.

## 2. Ролі P0
- `soldier`
- `commander`
- `medic_psych`
- `admin`

## 3. Рівні контролю доступу
- Route-level
- Action-level
- Scope-level
- Field-level

## 4. Scope model
### 4.1 Self scope
Користувач бачить і змінює лише власні дані.

### 4.2 Unit scope
Користувач бачить лише тих користувачів, які належать до його unit.

### 4.3 Admin scope
Admin керує доступом, ролями, units, audit. Але не має автоматичного повного доступу до чутливих psychological/case details.

## 5. Route access matrix
### 5.1 Shared routes
- auth/google/start: усі ролі
- auth/google/callback: усі ролі
- auth/me: усі ролі
- auth/select-role: усі ролі
- auth/refresh: усі ролі
- auth/logout: усі ролі

### 5.2 Soldier routes
- soldier/onboarding-status: soldier only
- soldier/baseline/*: soldier only
- soldier/daily-checkins*: soldier only
- soldier/weekly/*: soldier only
- soldier/cognitive/*: soldier only
- soldier/completion-summary: soldier only

### 5.3 Commander routes
- commander/dashboard/summary: commander only
- commander/dashboard/cases: commander only
- commander/cases/{user_id}: commander only

### 5.4 Medic routes
- medic/cases: medic only
- medic/cases/{case_review_id}: medic only
- medic/cases/{case_review_id} PATCH: medic only
- medic/cases/{case_review_id}/notes: medic only

### 5.5 Admin routes
- admin/users*: admin only
- admin/units*: admin only
- admin/audit-logs: admin only

## 6. Action matrix
### 6.1 Soldier
Allowed:
- пройти baseline
- подати daily check-in
- подати weekly шкали
- подати cognitive tests
- бачити власний completion state
- бачити власний risk status

Not allowed:
- бачити raw AI analysis
- бачити internal rule hits
- бачити чужі кейси

#### Soldier field policy
Soldier бачить:
- свої submitted values
- факт збереження
- `last_risk_status`
- коротке `explanation_text`
- due-state

Soldier не бачить:
- `current_risk_score`
- `risk_rule_hits`
- `hard_flag` internal code
- `confidence_score`
- `markers`
- `summary_for_system`
- case notes

### 6.2 Commander
Allowed:
- бачити summary dashboard
- бачити cases list
- бачити commander case card

Not allowed:
- medic notes
- редагувати case status
- створювати користувачів

#### Commander field policy
Commander бачить:
- `user_id`
- `full_name`
- `unit_id`
- `current_risk_status`
- коротке `explanation_text`
- high-level recent trend
- completion / recency indicators

Commander не бачить:
- повні відповіді PHQ-4/PSS-4 по item-level
- raw cognitive payload
- raw AI JSON
- `confidence_score`
- case notes
- службові коментарі медика/психолога

### 6.3 Medic / psychologist
Allowed:
- бачити priority cases list
- бачити detailed case
- змінювати case status
- додавати case notes
- бачити detailed signals
- бачити AI marker output
- бачити risk score and rule explanation

#### Medic field policy
Medic бачить:
- latest daily values
- latest weekly totals
- latest cognitive metrics
- AI markers
- `summary_for_system`
- `parse_status`
- `current_risk_score`
- `current_risk_status`
- `explanation_text`
- case notes
- case status

### 6.4 Admin
Allowed:
- створювати user
- змінювати roles
- генерувати invite
- deactivate/reactivate user
- керувати units
- бачити audit logs

Не allowed by default:
- detailed psych case content
- medic notes

Користувач із кількома ролями бачить лише те, що дозволено його `active_role`, а не об’єднання всіх ролей.

## 7. Active role rules
### 7.1 Після логіну
- якщо роль одна → активується автоматично
- якщо ролей кілька → обов’язковий role selection screen

### 7.2 У межах сесії
- доступ до route/API визначається тільки `active_role`
- на кожен request сервер перевіряє `session.active_role`
- frontend guards — це UX, не безпека

### 7.3 Role switching
Після switch:
- старі role-scoped cached data треба скидати
- новий active role створює новий permission context
- подія має логуватись в audit

## 8. Scope enforcement rules
### Soldier
`requested_user_id must equal authenticated_user.id`

### Commander
`target_user.unit_id == commander.unit_id`

### Medic / psychologist
`case.user.unit_id == medic.unit_id`

### Admin
Admin працює із users/roles/invites/units/audit і не відкриває автоматично доступ до medic case payloads.

## 9. Object-by-object matrix
### Users
- soldier: read self basic profile only
- commander: limited read in unit
- medic: limited read in unit
- admin: full admin read/create/update/deactivate

### User roles
- read own roles: усі
- assign roles to others: admin only

### Invites
- create/revoke invite: admin only

### Daily check-ins
- create self: soldier only
- read others summary: commander limited, medic via case scope, admin no

### Weekly assessments
- create self: soldier only
- read others: commander totals only via explanation/trend, medic in case scope, admin no

### Cognitive tests
- create self: soldier only
- read self limited, medic in case scope, commander only through summary

### AI analyses
- raw read: medic only
- summary only: commander via explanation, soldier no raw

### Risk statuses / events
- soldier read current self
- commander read current others in unit
- medic read current others in unit
- raw rule hits: medic only

### Case reviews
- read/update/add notes: medic only in unit
- create: internal/system only

### Audit logs
- read: admin only
- create: system/internal

## 10. Minimum backend permission rules
- valid session
- user.status = active
- session.status = active
- session.expires_at > now()
- `session.active_role == required_role`
- `required_role in user.assigned_roles`
- scope check on target object
- field filtering in response serializer

## 11. Audit requirements by action
### Auth/security
- login success/failure
- logout
- role selected
- role switched
- invite used
- access denied

### Admin
- user created
- roles changed
- invite generated
- user deactivated/reactivated
- unit created/updated

### Clinical workflow
- case opened
- case status changed
- note added

## 12. Edge cases
- multi-role leakage
- deactivated user with alive session
- commander overreach into medic endpoint
- admin overreach into case notes
- frontend-only restriction bug
