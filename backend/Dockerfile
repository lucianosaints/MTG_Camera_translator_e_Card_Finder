# Dockerfile otimizado e seguro para Django (MTG Camera Translator)

# Utilizando imagem oficial e enxuta do Python
FROM python:3.12-slim

# Evita que o Python grave arquivos .pyc e força logs diretamente no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para a aplicação
# - libmagic1 é obrigatório para o pacote 'python-magic' funcionar no Linux
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Cria um usuário não-root (prática de segurança essencial)
RUN addgroup --system django && adduser --system --ingroup django django

# Copia e instala as dependências Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte da aplicação
COPY . /app/

# Dá permissões aos arquivos para o usuário não-root
RUN chown -R django:django /app

# Muda para o usuário não-root criado
USER django

# Coleta arquivos estáticos (útil se estiver rodando com WhiteNoise)
# (Pode falhar se o settings.py depender de variáveis de ambiente não setadas aqui,
# por isso em alguns fluxos isso é feito no entrypoint, mas deixamos preparado)
# RUN python manage.py collectstatic --noinput

# Expõe a porta em que o gunicorn vai rodar
EXPOSE 8000

# Executa a aplicação usando o Gunicorn em vez do servidor de desenvolvimento
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "mtg_translator.wsgi:application"]
