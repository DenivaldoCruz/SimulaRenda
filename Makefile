.PHONY: install dev test lint build migrate

install:
	cd frontend && python -m pip install nicegui httpx pytest
	cd backend && python -m pip install -e ".[test]"

dev:
	docker compose up --build

test:
	cd frontend && pytest
	cd backend && pytest

lint:
	cd frontend && python -m compileall app
	cd backend && python -m compileall app

build:
	docker compose build

migrate:
	cd backend && alembic upgrade head
