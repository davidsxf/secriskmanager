#!/bin/bash
# 容器启动入口：运行迁移 → 收集静态文件 → 启动 gunicorn
set -e

cd /app

echo "==> 运行数据库迁移..."
uv run python manage.py migrate --noinput --settings=secriskmanager.settings.prod 2>/dev/null || \
    uv run python manage.py migrate --noinput --settings=secriskmanager.settings.dev

echo "==> 收集静态文件..."
uv run python manage.py collectstatic --noinput 2>/dev/null || true

echo "==> 启动 gunicorn..."
exec uv run gunicorn secriskmanager.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
