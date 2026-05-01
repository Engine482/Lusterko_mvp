# Dev Environment on One Hetzner VPS

Ціль: один Hetzner VPS використовується як dev host зараз і як основа для майбутнього deploy, але через окремі контури середовища.

## 1. Мінімальна рекомендована конфігурація VPS

- Ubuntu 24.04 LTS
- 4 vCPU мінімум
- 8 GB RAM мінімум; краще 16 GB
- NVMe SSD від 80 GB
- статична IPv4
- SSH доступ по ключу

## 2. Базова підготовка сервера

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl unzip build-essential ca-certificates gnupg lsb-release   python3 python3-venv python3-pip postgresql postgresql-contrib nginx redis-server
```

Опціонально:
- `ufw`
- `fail2ban`
- `certbot`

## 3. Користувач для розробки

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
```

Краще працювати не від `root`.

## 4. Node.js

Рекомендовано через `nvm` або NodeSource. Для простоти:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

## 5. Python backend env

```bash
cd ~/projects/lusterko/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

## 6. PostgreSQL

Створити окремі БД:
- `lusterko_dev`
- `lusterko_test`
- згодом `lusterko_prod`

```bash
sudo -u postgres psql
CREATE USER lusterko WITH PASSWORD 'change_me';
CREATE DATABASE lusterko_dev OWNER lusterko;
CREATE DATABASE lusterko_test OWNER lusterko;
CREATE DATABASE lusterko_prod OWNER lusterko;
\q
```

## 7. Логічне розділення середовищ на одному VPS

Навіть на одному VPS розділяй:
- `.env.dev`
- `.env.test`
- `.env.prod`
- окремі databases
- окремі systemd services
- окремі nginx server blocks, якщо треба

## 8. Рекомендована директорія на сервері

```text
/home/deploy/projects/lusterko/
├── backend/
├── frontend/
├── docs/
├── infra/
└── scripts/
```

## 9. Секрети

Не тримати секрети в git.
Тримати в:
- `.env.*`
- або systemd `EnvironmentFile=`

## 10. Мінімальні dev сервіси

На старті досить:
- Postgres
- backend dev server
- frontend dev server

У dev режимі не треба одразу будувати складний orchestration stack.
