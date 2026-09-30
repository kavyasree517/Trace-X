.PHONY: setup dev test lint typecheck migrate seed eval build clean

setup:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

dev:
	docker-compose up

test:
	cd backend && pytest --cov=app --cov-report=term-missing
	cd frontend && npm test

lint:
	cd backend && ruff check .
	python scripts/lint_copy.py
	python scripts/check_characters.py
	cd frontend && npm run lint

typecheck:
	cd backend && mypy app
	cd frontend && npm run typecheck

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.attribution.seed

eval:
	cd backend && python -m app.evaluation.run_all

build:
	cd backend && pip install -e .
	cd frontend && npm run build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf backend/dist frontend/dist
