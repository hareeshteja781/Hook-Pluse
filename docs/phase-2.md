# Phase 2 — Environment and Local Services

## Local runtime

- PostgreSQL 17
- Redis 7
- Docker Compose
- Python 3.13
- Node.js 24

## Containers

Docker Compose manages isolated PostgreSQL and Redis services with persistent named volumes and health checks.

## Development rule

Application containers are introduced after the backend foundation is created. This keeps Phase 2 focused on the local infrastructure required by later phases.
