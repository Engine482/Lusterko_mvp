# Deployment Environment on One Hetzner VPS

Ціль: той самий VPS використовується для майбутнього deploy MVP, але без хаосу між dev і prod.

## 1. Принцип

Один сервер допустимий для MVP, якщо є розділення:
- окремі env files
- окремі DB
- окремі systemd units
- окремі runtime порти
- окремий nginx reverse proxy layer

## 2. Рекомендований runtime stack

- Nginx
- FastAPI через `uvicorn` або `gunicorn + uvicorn workers`
- Next.js через `next start`
- PostgreSQL local service
- Redis опційно
- systemd для process management

## 3. Орієнтовна схема портів

- frontend prod: `127.0.0.1:3000`
- backend prod: `127.0.0.1:8000`
- frontend dev: `127.0.0.1:3001`
- backend dev: `127.0.0.1:8001`

Nginx публічно віддає тільки 80/443.

## 4. systemd units

Рекомендовано мати окремо:
- `lusterko-backend.service`
- `lusterko-frontend.service`
- за потреби dev-версії як тимчасові юніти або запуск вручну

## 5. Nginx reverse proxy

Публічний домен:
- `/` → frontend
- `/api/` → backend

## 6. TLS

Для MVP досить Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```

## 7. Deploy strategy

MVP-адекватно:
- git pull
- install deps
- run migrations
- restart backend
- rebuild/restart frontend

Краще через один deploy script.

## 8. Backup minimum

Потрібно мінімум:
- щоденний `pg_dump` prod DB
- копія `.env.prod`
- копія `infra/` конфігів

## 9. Логи

Джерела логів:
- `journalctl -u lusterko-backend`
- `journalctl -u lusterko-frontend`
- nginx logs
- app structured logs

## 10. Що не треба зараз

- Kubernetes
- Docker swarm
- microservices split
- blue/green deployment
- складний IaC

Для P0 це зайве.
