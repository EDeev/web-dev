# Экзаменационное приложение курса (ex/, сайт ex-web): Flask + SQLite за gunicorn
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY ex/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY ex/ .
# копия скриптов базы — том /app/db при первом запуске пустой
RUN cp -r db /opt/db-seed
COPY docker/entrypoint.sh /entrypoint.sh
EXPOSE 8000
VOLUME ["/app/db", "/app/app/static/uploads"]
ENTRYPOINT ["sh", "/entrypoint.sh"]
