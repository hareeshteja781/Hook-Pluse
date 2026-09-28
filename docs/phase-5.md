# Phase 5 — Redis Streams and Delivery

Events are persisted in PostgreSQL first with status `RECEIVED`.
The dispatcher moves received events into the Redis Stream `hookpluse:webhook_events` and marks them `QUEUED`.
The consumer group `hookpluse-delivery` claims queued events and marks each event `DELIVERING` before delivery.
Successful 2xx responses produce `DELIVERED`; non-2xx responses and transport failures produce `FAILED`.
Each delivery is recorded in `delivery_attempts`.

Retry scheduling and the dead-letter queue are implemented in Phase 6.
