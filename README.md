# Marketplace Datak

## Services

- `b2b`: marketplace for interactions between companies
- `b2c`: marketplace for interactions between companies and customers
- `moderation`: moderation service
- `frontend`: shared React frontend

## Setup
1. Install `uv` according [docs](https://docs.astral.sh/uv/getting-started/installation/)
2. Install python dependencies: `uv sync --frozen`
3. Install `pre-commit` hooks: `pre-commit install`

Also you can use `make init` after `uv` installation

## Local environment
1. Copy .env.example to .env and fill environment variables
2. Run all services locally with docker compose: `docker compose up -d`
