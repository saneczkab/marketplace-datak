up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build --no-cache

migrate:
	docker-compose exec app alembic upgrade head

migration:
	docker-compose exec app alembic revision --autogenerate -m "$(name)"