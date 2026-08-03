build:
	docker compose -f ./services/b2b/docker-compose.yml -f ./services/b2c/docker-compose.yml -f ./services/moderation/docker-compose.yml -f ./services/frontend/docker-compose.yml build --no-cache
up:
	docker compose up -d
down:
	docker compose down

migrate:
	docker compose exec b2b-backend uv run alembic -c /app/database/alembic.ini upgrade head
	docker compose exec b2c-backend uv run alembic -c /app/database/alembic.ini upgrade head

init:
	uv sync --frozen
	uv run pre-commit install
