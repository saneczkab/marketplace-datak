up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

migrate:
	docker-compose exec b2c-backend uv run alembic -c /app/database/alembic.ini upgrade head

migration:
	docker-compose exec b2c-backend uv run alembic -c /app/database/alembic.ini revision --autogenerate -m "$(name)"

format:
	uv run ruff format .
