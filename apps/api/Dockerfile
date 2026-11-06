FROM python:3.12-slim
WORKDIR /app
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api/app.py ./app.py
COPY apps/api/demo_seed.py ./demo_seed.py
COPY apps/api/property_runtime.py ./property_runtime.py
COPY apps/api/property_template.html ./property_template.html
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app:app --host 0.0.0.0 --port 8000 --proxy-headers "]
