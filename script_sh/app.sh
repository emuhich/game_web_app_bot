#! /bin/bash

set -e

alembic upgrade head

# создаём/обновляем админа из переменных окружения
python /api/create_admin.py || echo "[WARN] create_admin.py failed"

gunicorn app.main:app --workers 4 --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker