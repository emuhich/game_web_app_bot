#! /bin/bash

set -e

alembic upgrade head

# создаём/обновляем админа из переменных окружения
python /api/create_admin.py || echo "[WARN] create_admin.py failed"

# Запускаем gunicorn/uvicorn, доверяя X-Forwarded-* заголовкам от всех прокси
exec gunicorn app.main:app \
  --workers 1 \
  --bind 0.0.0.0:8000 \
  --worker-class uvicorn.workers.UvicornWorker \
  --forwarded-allow-ips="*"
