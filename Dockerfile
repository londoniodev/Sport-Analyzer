# ══════════════════════════════════════════════════════════════
# SPORTS PREDICTOR - Dockerfile de Producción (React + FastAPI)
# ══════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────
# STAGE 1: Frontend Builder (React + Vite + Tailwind CSS)
# ──────────────────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Instalar pnpm
RUN npm install -g pnpm

# Copiar configuración del frontend
COPY frontend/package.json frontend/pnpm-lock.yaml* ./
RUN pnpm install

# Copiar código del frontend y compilar
COPY frontend/ ./
RUN pnpm run build

# ──────────────────────────────────────────────────────────────
# STAGE 2: Backend Builder (Python dependencies)
# ──────────────────────────────────────────────────────────────
FROM python:3.10-slim AS backend-builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt fastapi uvicorn

# ──────────────────────────────────────────────────────────────
# STAGE 3: Final Production Image
# ──────────────────────────────────────────────────────────────
FROM python:3.10-slim AS production

WORKDIR /app

# Instalar librerías runtime requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar librerías de Python desde backend-builder
COPY --from=backend-builder /root/.local /root/.local

# Asegurar PATH
ENV PATH=/root/.local/bin:$PATH

# Copiar el frontend compilado
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Copiar el backend de Python
COPY app/ ./app/

# Exponer el puerto de la API y Frontend (FastAPI)
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Lanzar FastAPI
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
