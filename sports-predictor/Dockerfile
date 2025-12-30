# ══════════════════════════════════════════════════════════════
# SPORTS PREDICTOR - Dockerfile de Producción
# Optimizado con multi-stage build para menor tamaño
# ══════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────
# STAGE 1: Builder - Instalar dependencias
# ──────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ──────────────────────────────────────────────────────────────
# STAGE 2: Production - Imagen final ligera
# ──────────────────────────────────────────────────────────────
FROM python:3.10-slim AS production

WORKDIR /app

# Instalar solo librerías runtime necesarias (sin compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar dependencias instaladas desde builder
COPY --from=builder /root/.local /root/.local

# Asegurar que los binarios estén en PATH
ENV PATH=/root/.local/bin:$PATH

# Copiar código de la aplicación
COPY app/ ./app/

# Configuración de Streamlit para producción
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Puerto expuesto
EXPOSE 8501

# Healthcheck para Coolify
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Ejecutar Streamlit
CMD ["streamlit", "run", "app/main.py"]
