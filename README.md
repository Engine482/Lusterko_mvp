# Lusterko — Developer Bootstrap Pack

Це bootstrap pack для старту розробки MVP «Люстерко» у Claude Code, Codex CLI, Cursor або руками через git repo.

## Що всередині

- `docs/01_product/PRD.md` — головний продуктовий документ у markdown
- `docs/00_index/Lusterko_Master_Index_v1.md` — навігація по пакету
- `docs/02_pre_build/` — pre-build документи
- `docs/03_planning/` — sprint plan і backlog
- `docs/04_environment/` — інструкції для dev і deploy на одному Hetzner VPS
- `docs/05_repo_and_agenting/` — інструкції для AI-агентів, repo structure і bootstrap sequence
- `sources/` — оригінальні PDF
- `AGENTS.md` — правила для AI coding agents
- `.gitignore` — стартовий ignore для monorepo Next.js + FastAPI + Postgres

## Рекомендований порядок читання

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
11. `docs/04_environment/DEV_ENV_HETZNER_VPS.md`
12. `docs/04_environment/DEPLOYMENT_ENV_HETZNER_VPS.md`
13. `docs/05_repo_and_agenting/BOOTSTRAP_PROMPT.md`

## Мінімальний результат цього пакета

Пакета достатньо, щоб:
- підняти repo
- налаштувати локальну/dev інфраструктуру на одному Hetzner VPS
- почати Sprint 0 і Sprint 1
- передати пакет Claude Code без втрати продуктової рамки

## Що не треба робити на старті

- не роздувати MVP новими фічами
- не розбивати P0 на мікросервіси
- не ускладнювати AI beyond comment parsing
- не додавати ще один auth provider
- не додавати аналітику V2+

## Рекомендована базова структура repo

```text
lusterko/
├── backend/
├── frontend/
├── docs/
├── infra/
├── scripts/
├── .env.example
├── .gitignore
├── README.md
└── AGENTS.md
```
