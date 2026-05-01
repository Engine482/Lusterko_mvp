# AGENTS.md — Lusterko

Цей файл призначений для Claude Code, Codex CLI, Cursor agents та інших AI coding agents.

## Місія

Ти не вигадуєш новий продукт. Ти реалізуєш уже визначений MVP «Люстерко».

## Пріоритет документів

У разі суперечностей дотримуйся такого порядку:

1. `docs/01_product/PRD.md`
2. `docs/00_index/Lusterko_Master_Index_v1.md`
3. `docs/02_pre_build/Lusterko_Risk_Engine_Spec_v1.md`
4. `docs/02_pre_build/Lusterko_API_Contracts_v1.md`
5. `docs/02_pre_build/Lusterko_DB_Schema_v1.md`
6. `docs/02_pre_build/Lusterko_RBAC_Matrix_v1.md`
7. `docs/02_pre_build/Lusterko_Wireframes_P0_v1.md`
8. `docs/02_pre_build/Lusterko_Test_Scenarios_P0_v1.md`
9. `docs/03_planning/Lusterko_Sprint_Plan_P0_v1.md`
10. `docs/03_planning/Lusterko_Development_Backlog_v1.md`

Якщо зміна стосується середовища або agenting, додатково звіряйся з:

- `docs/04_environment/`
- `docs/05_repo_and_agenting/`
- `.mcp.json`

## Scope discipline

P0 MVP включає тільки:
- invite-based auth
- Google OAuth
- role selection + role switching
- soldier baseline / daily / weekly / cognitive
- AI text parsing лише для optional comment
- rule-based Risk Engine
- commander dashboard
- medic case workflow
- admin control
- audit trail

Не додавати:
- extra auth providers
- notification center
- wearables
- predictive ML
- voice analytics
- microservices
- complex analytics V2+
- chatbot behavior

## Архітектурна рамка

- Frontend: Next.js
- Backend: FastAPI
- DB: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- API: REST JSON
- Deploy: один Hetzner VPS для dev + майбутнього deploy контуру з окремими environment profiles

## Робочий стиль

Перед будь-якою великою зміною:
1. звірся з релевантними документами
2. коротко зафіксуй, що саме робиш
3. реалізуй мінімальний вертикальний зріз
4. перевір API / DB / RBAC / tests

Не генеруй продуктовий код, якщо задача явно про bootstrap, repo hygiene або середовище. Для P0 тримайся документації та не додавай нові сервіси без окремого рішення.

## Безпека

- будь-яке role/scope обмеження має бути на backend
- frontend guards не вважаються захистом
- admin не дорівнює omniscient superuser
- active role визначає доступ, а не сумарний набір ролей
- секрети мають жити тільки в локальних `.env*` або runtime environment
- не коміть токени, production passwords, dumps або приватні ключі
- Claude Code MCP integrations мають бути project-scoped через `.mcp.json` або `claude mcp`; не додавай filesystem/git MCP чи випадкові community integrations без явної потреби

## Що робити першим

1. Прочитати `docs/01_product/PRD.md`
2. Прочитати `docs/00_index/Lusterko_Master_Index_v1.md`
3. Прочитати pre-build документи
4. Виконувати Sprint 0 → Sprint 5 послідовно
