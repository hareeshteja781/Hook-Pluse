# Hook Pluse

Event-driven webhook platform built phase-by-phase.

## Build Phases

1. Project structure + initial files
2. Environment + Docker + PostgreSQL + Redis
3. Backend foundation + database + authentication
4. Webhook ingestion + HMAC + idempotency
5. Redis Streams + background worker + delivery
6. Retry + exponential backoff + DLQ
7. React frontend + dashboard
8. WebSockets + real-time events
9. Event Inspector + Monaco + Replay
10. Metrics + simulator
11. Testing + CI/CD + security
12. Final integration + deployment verification

## Repository Layout

- backend/ — FastAPI API and application services
- worker/ — Background event processing worker
- frontend/ — React web application
- docs/ — Architecture and project documentation
- scripts/ — Local development and maintenance scripts
- infra/ — Infrastructure-related configuration

Each phase should leave the project in a runnable and verifiable state before the next phase begins.
