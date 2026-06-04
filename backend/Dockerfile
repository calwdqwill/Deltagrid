FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./alembic.ini
COPY app ./app

ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://deltagrid:deltagrid@postgres:5432/deltagrid

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
