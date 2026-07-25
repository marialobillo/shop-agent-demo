FROM python:3.13-slim

# Crear usuario no root
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

WORKDIR /app

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Copiar archivos de proyecto
COPY pyproject.toml uv.lock* ./

# Instalar dependencias con uv
RUN uv pip install --no-cache-dir -r pyproject.toml

# Copiar el código
COPY src/ ./src/

# Cambiar ownership al usuario no root
RUN chown -R appuser:appgroup /app

# Cambiar al usuario no root
USER appuser

EXPOSE 8000

# Ruta completa al main.py
CMD ["uvicorn", "src.tienda.api.main:app", "--host", "0.0.0.0", "--port", "8000"]