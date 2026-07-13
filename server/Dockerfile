FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./app
COPY docs /app/docs
RUN mkdir -p /app/data

ENV DATABASE_URL=sqlite+aiosqlite:////app/data/command_center.db
ENV VAULT_PATH=/app/vault

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
