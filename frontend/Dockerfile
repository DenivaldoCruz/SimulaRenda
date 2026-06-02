FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BACKEND_API_URL=http://backend:8000/api/v1
COPY pyproject.toml ./
RUN pip install --no-cache-dir nicegui httpx
COPY app ./app
EXPOSE 5173
CMD ["python", "-m", "app.main"]
