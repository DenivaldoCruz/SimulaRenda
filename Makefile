.PHONY: install dev test lint build migrate

install:
	cd backend && python -m pip install -e ".[dev]"

dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && pytest --cov=app --cov-report=term-missing

lint:
	cd backend && ruff check app/ && mypy app/

build:
	cd backend && python -m compileall app

migrate:
	cd backend && alembic upgrade head
