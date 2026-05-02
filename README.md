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
- `.env.example` — шаблон локальних змінних без секретів
- `infra/docker-compose.yml` — локальний PostgreSQL для dev

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
13. `docs/04_environment/DEV_PROD_SAME_MAC_MINI.md`
14. `docs/05_repo_and_agenting/BOOTSTRAP_PROMPT.md`

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

## Dev commands

```bash
make setup
make db-up
make lint
make test
make run
```

`make run` is intentionally a placeholder until product code exists. Backend dependencies are managed with `uv` in `backend/`; frontend uses `pnpm` in `frontend/`.

## Local services

Only PostgreSQL is defined for now:

```bash
make db-up
make db-down
```

Copy `.env.example` to a local `.env` when real credentials are needed. Do not commit `.env` or secret values.

## Claude Code MCP

Project-scoped MCP config lives in `.mcp.json` and includes only:

- `github` for repository, PR, issues, and workflow context via GitHub's official MCP endpoint.
- `postgres` for read-only schema inspection and smoke queries against the local database.

Set `GITHUB_MCP_PAT` and `LUSTERKO_DATABASE_URL` in your shell or local `.env` before using those integrations.

## Production deployment

Pilot target: a single VPS at `lusterko.motornyi.com`. The production stack is
`infra/docker-compose.prod.yml` (postgres + backend + frontend) fronted by
host-level nginx + Let's Encrypt.

### One-time host setup

1. **DNS.** Point an `A` record `lusterko.motornyi.com` → VPS IP.
2. **Packages.** Install Docker Engine + the compose plugin, plus `nginx` and
   `certbot` (with `python3-certbot-nginx`).
3. **Repo.** `git clone` this repo into `/opt/lusterko_mvp` (path is just a
   convention; `scripts/deploy.sh` runs from the repo root).
4. **Env file.** Copy `.env.production.example` → `.env.production` and fill
   in real secrets (`POSTGRES_PASSWORD`, `DATABASE_URL`, Google OAuth client,
   SMTP credentials). Never commit this file.
5. **Google OAuth.** Create a real OAuth client in Google Cloud Console; set
   the authorized redirect URI to
   `https://lusterko.motornyi.com/api/v1/auth/google/callback` and put its
   client id/secret into `.env.production`.
6. **Nginx vhost.** Copy `infra/nginx/lusterko.conf` to
   `/etc/nginx/sites-available/lusterko.conf`, symlink to
   `/etc/nginx/sites-enabled/`, and `nginx -t && systemctl reload nginx`.
7. **TLS.** First-time certificate:
   ```bash
   certbot --nginx -d lusterko.motornyi.com
   ```
   Certbot installs its own systemd timer; renewals are automatic. The vhost
   serves `/.well-known/acme-challenge/` from `/var/www/certbot` for renewals.
8. **Bootstrap admin.** Bring postgres up, migrate, and seed the pilot admin
   with all roles:
   ```bash
   docker compose --env-file .env.production -f infra/docker-compose.prod.yml up -d postgres
   docker compose --env-file .env.production -f infra/docker-compose.prod.yml run --rm \
     -e ADMIN_EMAIL=motorny.v@gmail.com \
     -e ADMIN_FULL_NAME="Motorny V." \
     -e SEED_UNIT_NAME="Тестовий підрозділ" \
     -e BOOTSTRAP_USER_ROLES=admin,soldier,commander,medic_psych \
     backend python -m scripts.seed
   ```

### Recurring deploy

```bash
./scripts/deploy.sh
```

`deploy.sh` pulls main, rebuilds backend + frontend images, runs alembic
migrations against the running postgres container, and recreates only the app
containers — postgres stays up across deploys.

### Backups

Daily `pg_dump` via cron (root):

```cron
15 3 * * * root /opt/lusterko_mvp/scripts/backup_db.sh >> /var/log/lusterko-backup.log 2>&1
```

Backups live under `/var/backups/lusterko/` (override with `BACKUP_DIR`).
Retention defaults to 14 days (`RETENTION_DAYS`).

### Sanity check

`make prod-build` runs `docker compose -f infra/docker-compose.prod.yml build`
locally — useful in CI or before a release to catch broken Dockerfiles.
