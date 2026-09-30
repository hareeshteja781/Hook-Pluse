# Hook Pluse

A full-stack webhook gateway and reliability platform for receiving, processing, delivering, retrying, monitoring, and replaying webhook events.

## Features
- Webhook endpoint management
- HMAC-SHA256 signature verification
- Idempotency checks
- Redis Streams for asynchronous processing
- Background workers for webhook delivery
- Timeout handling and exponential backoff retries
- Dead-Letter Queue (DLQ) support
- Redis Pub/Sub and WebSockets for real-time updates
- Event inspection and replay with Monaco Editor
- Delivery history and event monitoring

## Tech Stack
- Backend: Python, FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React, TypeScript, Vite, React Router
- Messaging: Redis, Redis Streams, Redis Pub/Sub
- Editor: Monaco Editor
- Infrastructure: Docker

## Architecture
```text
frontend/   React + TypeScript application
backend/    FastAPI API and application services
worker/     Background event processing
docs/       Project documentation
scripts/    Local development and test utilities
infra/      Infrastructure configuration
```

PostgreSQL stores application and delivery data. Redis provides asynchronous event processing and real-time messaging.

## Run Locally
```bash
docker compose up -d
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

In another terminal:
```bash
cd frontend
npm install
npm run dev
```
