.PHONY: install dev test lint build migrate

install:
	cd frontend && npm install
	cd backend && python -m pip install -e ".[test]"

dev:
	docker compose up --build

test:
	cd frontend && npm test -- --run
	cd backend && pytest

lint:
	cd frontend && npm run lint
	cd backend && python -m compileall app

build:
	cd frontend && npm run build
	docker compose build

migrate:
	cd backend && alembic upgrade head
