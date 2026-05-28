# ══════════════════════════════════════════════════════════════
# SPORTS PREDICTOR - Dockerfile.frontend (Solo React)
# ══════════════════════════════════════════════════════════════

# STAGE 1: Compilar la aplicación React
FROM node:20-slim AS builder

WORKDIR /app

# Instalar pnpm
RUN npm install -g pnpm

# Instalar dependencias
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

# Copiar el código del frontend y compilar
COPY . .
RUN pnpm run build

# STAGE 2: Servir con Nginx (producción súper ligera)
FROM nginx:alpine

# Copiar los estáticos al directorio de Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de Nginx para SPA (manejo de rutas de React Router)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
