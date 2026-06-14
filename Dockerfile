# SecRiskManager - 生产部署镜像
# 基于 Python 3.12-slim，使用 SQLite，单容器部署

FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 复制依赖配置
COPY pyproject.toml uv.lock* ./

# 安装生产依赖
RUN uv sync --no-dev --frozen

# 复制项目代码
COPY . .

# 创建数据目录（SQLite 存放位置）
RUN mkdir -p /app/data /app/backups /app/staticfiles

# 构建 Tailwind CSS
RUN uv run python build_tailwind.py 2>/dev/null || true

# 收集静态文件
RUN uv run python manage.py collectstatic --noinput --settings=secriskmanager.settings.prod 2>/dev/null || \
    uv run python manage.py collectstatic --noinput --settings=secriskmanager.settings.dev

# 数据卷
VOLUME ["/app/data", "/app/backups"]

EXPOSE 8000

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
