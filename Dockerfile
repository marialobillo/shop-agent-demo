FROM python:3.13-slim

# Instalar uv (versión pineada, no :latest, para builds reproducibles)
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/

# Crear usuario no-root
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1) Copiar SOLO los ficheros de dependencias primero (cacheo de capas)
COPY pyproject.toml uv.lock ./

# 2) Instalar dependencias según el lock, sin dev, sin instalar aún el proyecto
RUN uv sync --locked --no-dev --no-install-project

# 3) Ahora el código, ya con el dueño correcto (evita un chown aparte)
COPY --chown=appuser:appgroup src/ ./src/
COPY pyproject.toml uv.lock README.md ./

# 4) Instalar el proyecto en sí (tienda) sobre las deps ya cacheadas
RUN uv sync --locked --no-dev --no-editable

USER appuser

EXPOSE 8000

# uv run ejecuta uvicorn desde el .venv que creó uv sync
# CMD ["uv", "run", "uvicorn", "tienda.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD [".venv/bin/uvicorn", "tienda.api.main:app", "--host", "0.0.0.0", "--port", "8000"]