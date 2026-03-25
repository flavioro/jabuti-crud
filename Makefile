install:
	pip install -e .[dev]

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

seed:
	python -m app.scripts.seed --count 50

test:
	pytest -q

lint:
	ruff check .
