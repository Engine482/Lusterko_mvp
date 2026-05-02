#!/usr/bin/env bash
# Daily pg_dump of the production Lusterko database (TASK-6202).
#
# Designed for cron on the host. Dumps run inside the postgres container
# (no client tools required on the host) and write a gzipped custom-format
# archive to BACKUP_DIR. Old backups beyond RETENTION_DAYS are deleted.
#
# Cron example (write to /etc/cron.d/lusterko-backup, root-owned):
#   15 3 * * * root /opt/lusterko_mvp/scripts/backup_db.sh >> /var/log/lusterko-backup.log 2>&1

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/lusterko}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
CONTAINER="${POSTGRES_CONTAINER:-lusterko-postgres-prod}"
DB_NAME="${POSTGRES_DB:-lusterko_prod}"
DB_USER="${POSTGRES_USER:-lusterko}"

mkdir -p "$BACKUP_DIR"

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="$BACKUP_DIR/lusterko-${stamp}.dump.gz"

echo "[backup] dumping ${DB_NAME} from ${CONTAINER} → ${out}"
docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc \
  | gzip -9 > "$out"

# Sanity: a custom-format dump compressed with gzip should be at least a few KB.
size=$(stat -c%s "$out" 2>/dev/null || stat -f%z "$out")
if [[ "$size" -lt 1024 ]]; then
  echo "[backup] dump suspiciously small (${size} bytes), keeping for inspection" >&2
  exit 2
fi

echo "[backup] pruning files older than ${RETENTION_DAYS}d"
find "$BACKUP_DIR" -type f -name 'lusterko-*.dump.gz' -mtime "+${RETENTION_DAYS}" -delete

echo "[backup] done"
