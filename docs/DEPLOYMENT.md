# Hook Pluse Deployment

## Local production-style stack

Use `docker-compose.full.yml` to run PostgreSQL, Redis, FastAPI, the worker, and the React/Nginx frontend together.

Required environment variables:

- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `WEBHOOK_HMAC_SECRET`

Do not commit real secrets. Create a local env file from `infra/compose.env.example`.

## Services

- Frontend: `http://localhost:8080`
- FastAPI: `http://localhost:8000`
- PostgreSQL: host port `5433`
- Redis: host port `6379`

## Database migration

Run the migration from the backend working directory with `python -m alembic upgrade head`.

## Production notes

`VITE_API_BASE_URL` is a frontend build-time setting. For a public deployment, set it to the deployed FastAPI base URL and configure the backend CORS origins for the deployed frontend origin.

Production mode rejects the default JWT and webhook secrets.

## Verification

Validate Compose with `docker compose -f docker-compose.full.yml config` and verify all containers are healthy before accepting the deployment.
