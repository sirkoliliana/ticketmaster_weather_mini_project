FROM python:3.11-slim AS base
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM base AS dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS test
RUN pip install pytest
CMD ["pytest"]

FROM base AS prod
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
