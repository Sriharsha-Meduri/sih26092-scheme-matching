FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_NO_CACHE_DIR=1     PYTHONPATH=/app

WORKDIR /app

# Build context is the repository root (see docker-compose.yml), so the
# intelligence engine and its knowledge base can be copied in beside the app.
COPY apps/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/backend/ ./
COPY intelligence/ ./intelligence/
COPY KB/ ./KB/

EXPOSE 8000

# Migrations and the seed run at container start so a fresh database is ready to demo.
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
