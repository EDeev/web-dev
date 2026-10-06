#!/bin/sh
# Первый запуск: база с ролями и тестовыми пользователями (пароли — из SEED_*_PASSWORD или случайные, в лог)
set -e
cp -n /opt/db-seed/* /app/db/ 2>/dev/null || true
[ -f /app/db/library.db ] || python db/db_seed.py
mkdir -p /app/app/static/uploads
exec gunicorn --workers 2 --bind 0.0.0.0:8000 app:app
