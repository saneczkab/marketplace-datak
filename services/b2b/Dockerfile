FROM python:3.12-slim

WORKDIR /app

COPY services/b2b/pyproject.toml uv.lock* ./

RUN uv sync --freeze

COPY services/b2b /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]