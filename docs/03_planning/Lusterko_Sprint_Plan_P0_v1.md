# Lusterko — Sprint Plan P0 v1

## 1. Принцип планування
P0 будується по вертикальних зрізах:
1. доступ і каркас
2. soldier data input
3. processing
4. role UIs
5. стабілізація

## 2. Definition of Done для P0
P0 вважається готовим, якщо:
- користувача можна створити, видати invite, увійти через Google
- multi-role user може вибрати роль і перемикати її
- soldier може пройти baseline
- soldier може пройти daily / weekly / cognitive
- коментар обробляється AI або безпечно падає у fallback
- Risk Engine перераховує статус і пояснення
- commander бачить dashboard і scoped cases
- medic бачить detailed case, може оновити статус і додати note
- admin керує users / roles / invites / units
- audit log фіксує критичні події
- P0-critical тести проходять

## 3. Загальна структура спринтів
- **Sprint 0** — Repo + Infra + Foundations
- **Sprint 1** — Auth + Access + Admin Basic
- **Sprint 2** — Soldier Baseline + Daily
- **Sprint 3** — Weekly + Cognitive + AI Parsing
- **Sprint 4** — Risk Engine + Commander
- **Sprint 5** — Medic + Audit + Stabilization

## 4. Sprint 0 — Repo + Infra + Foundations
### Goal
Підняти каркас.

### Deliverables
- monorepo або `backend/` + `frontend/`
- dev environment
- PostgreSQL local/staging
- migration setup
- base FastAPI app
- base Next.js app
- env management
- CI minimal
- seed framework
- shared constants/enums
- skeleton audit logger

### Done criteria
- backend and frontend run locally
- DB migrations apply cleanly
- seeded users exist
- base protected routes reachable
- CI runs lint/test placeholder

## 5. Sprint 1 — Auth + Access + Admin Basic
### Goal
Зібрати керований доступ у систему.

### Deliverables
- invite flow
- Google OAuth
- session management
- active role selection
- role switching
- admin basic user management
- unit management
- invite generation
- deactivate/reactivate

### Done criteria
- admin can create user and issue invite
- invited user can sign in
- multi-role user can choose and switch role
- deactivated user blocked
- audit events created

## 6. Sprint 2 — Soldier Baseline + Daily
### Goal
Зібрати soldier-side core input loop.

### Deliverables
- soldier home
- onboarding status
- full baseline flow
- baseline completion
- daily check-in
- daily success/confirmation
- completion summary basic

### Done criteria
- soldier can complete baseline end-to-end
- soldier can submit one daily per day
- soldier sees due-state correctly
- invalid inputs rejected

## 7. Sprint 3 — Weekly + Cognitive + AI Parsing
### Goal
Додати всі решта input-шари і зібрати assessment framework.

### Deliverables
- weekly reassessment
- cognitive launcher
- reaction test flow
- go/no-go flow
- internal AI parse service
- AI fallback behavior

### Done criteria
- weekly and cognitive submissions work
- AI returns structured output
- AI failure does not break daily save
- due states reflect weekly/cognitive availability

## 8. Sprint 4 — Risk Engine + Commander
### Goal
Перетворити input data на risk output і управлінський огляд.

### Deliverables
- risk computation service
- rule hits persistence
- current risk status persistence
- explanation generation
- commander dashboard
- commander cases list/card

### Done criteria
- risk status recalculates reliably
- commander sees own unit only
- explanations shown correctly
- hard flags override score thresholds

## 9. Sprint 5 — Medic + Audit + Stabilization
### Goal
Замкнути case workflow, аудит і довести P0 до demo/internal-test ready.

### Deliverables
- case auto-open logic
- medic cases list
- detailed case screen
- add note
- update case status
- admin audit screen
- regression fixes
- smoke pass

### Done criteria
- medic can work end-to-end with cases
- audit logs visible to admin
- no critical RBAC leaks
- all P0-critical tests pass

## 10. Parallel workstreams
- Stream A — Backend core
- Stream B — Frontend screens
- Stream C — Test/fixtures
- Stream D — Product integration

## 11. Backlog structure inside each sprint
1. Schema first
2. Service logic
3. API layer
4. UI layer
5. Integration
6. Tests

## 12. Minimal task board columns
- `Backlog`
- `Ready`
- `In progress`
- `Blocked`
- `Review`
- `Done`

## 13. Recommended epic map
- EPIC-01 Auth & Access
- EPIC-02 Admin Module
- EPIC-03 Soldier Assessments
- EPIC-04 AI Parsing
- EPIC-05 Risk Engine
- EPIC-06 Commander Module
- EPIC-07 Medic Case Review
- EPIC-08 Audit & Security
- EPIC-09 UI Infrastructure
- EPIC-10 Test Harness & Seed Data

## 14. Release gates
- Gate 1 — After Sprint 1: можна заходити в систему та управляти доступом
- Gate 2 — After Sprint 2: є базовий soldier loop
- Gate 3 — After Sprint 3: усі data input layers працюють
- Gate 4 — After Sprint 4: система реально починає рахувати ризик і показувати його командиру
- Gate 5 — After Sprint 5: є повний P0 контур для internal demo/testing

## 15. Що НЕ робити в P0
- notification center
- complex analytics
- AI beyond comment parsing
- extra auth providers
- microservices
- heavy design polish before stable flows
- V2 calibration features

## 16. Найбільші ризики execution
- scope creep
- frontend drifting from wireframes
- backend drifting from API contracts
- AI overfocus
- RBAC shortcuts
- weak test discipline
