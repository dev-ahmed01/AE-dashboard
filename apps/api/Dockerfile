FROM python:3.12-slim
WORKDIR /app
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Include all application Python modules, including future helpers like editor_preview.py.
COPY apps/api/*.py ./
COPY apps/api/property_template.html ./property_template.html
COPY apps/api/property_master.html ./property_master.html
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin accom
USER accom
EXPOSE 8000
# Migrations are an approved one-off release task, never an API startup side effect.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
