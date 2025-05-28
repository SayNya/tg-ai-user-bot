run:
	poetry run python -m src.main

generate:
	poetry run alembic revision --autogenerate -m "$(m)"

migrate:
	poetry run alembic upgrade head
