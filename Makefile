up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

migrate:
	docker-compose exec b2b-backend uv run alembic -c /app/database/alembic.ini upgrade head

migration:
	docker-compose exec b2b-backend uv run alembic -c /app/database/alembic.ini revision --autogenerate -m "$(name)"