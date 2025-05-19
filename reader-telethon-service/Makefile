PROJECT_DIR=src

format:
	poetry run python -m isort $(PROJECT_DIR)
	poetry run python -m black $(PROJECT_DIR) --config pyproject.toml

run:
	poetry run python -m src.main
	