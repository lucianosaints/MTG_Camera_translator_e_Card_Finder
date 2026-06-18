# Dockerfile Unificado (MTG Camera Translator)

# ESTÁGIO 1: Build do Frontend (React/Vite)
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
# Copia apenas os arquivos de dependência primeiro para aproveitar o cache do Docker
COPY frontend/package*.json ./
RUN npm install
# Copia o restante do código do frontend e faz o build
COPY frontend/ ./
RUN npm run build

# ESTÁGIO 2: Backend (Django) e Montagem Final
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/data/db.sqlite3

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root
RUN addgroup --system django && adduser --system --ingroup django django

# Instala as dependências do Python
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn whitenoise

# Copia o código do backend
COPY backend/ /app/

# Copia a pasta 'dist' gerada no estágio 1 (Frontend) para dentro da estrutura esperada pelo Django
# No nosso settings.py, o Django espera encontrar em BASE_DIR.parent / 'frontend' / 'dist'
# Como o BASE_DIR é /app, vamos criar /frontend/dist no mesmo nível ou configurar
RUN mkdir -p /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Cria diretórios necessários para volume e mídia
RUN mkdir -p /data /app/media /app/staticfiles /app/logs
RUN chown -R django:django /app /data

USER django

EXPOSE 8000

# Script de inicialização (Roda as migrações e sobe o Gunicorn)
CMD sh -c "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 2 mtg_translator.wsgi:application"
