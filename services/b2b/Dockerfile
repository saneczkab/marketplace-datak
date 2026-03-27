FROM python:3.12-slim

WORKDIR /app

COPY services/b2b/pyproject.toml .

RUN pip install --no-cache-dir fastapi uvicorn

COPY services/b2b /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]