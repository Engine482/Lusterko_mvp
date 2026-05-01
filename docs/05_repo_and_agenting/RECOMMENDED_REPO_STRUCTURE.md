# Recommended Repo Structure

```text
lusterko/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── modules/
│   │       ├── auth/
│   │       ├── users/
│   │       ├── assessments/
│   │       ├── ai/
│   │       ├── risk/
│   │       ├── cases/
│   │       └── audit/
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── auth/
│   │   ├── soldier/
│   │   ├── commander/
│   │   ├── medic/
│   │   └── admin/
│   ├── components/
│   ├── lib/
│   ├── types/
│   ├── tests/
│   ├── package.json
│   └── .env.example
│
├── docs/
├── infra/
│   ├── nginx/
│   ├── systemd/
│   └── deploy/
├── scripts/
├── .gitignore
├── README.md
└── AGENTS.md
```
