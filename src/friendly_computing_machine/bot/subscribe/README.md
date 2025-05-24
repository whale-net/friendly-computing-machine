# ManMan Subscribe Service

The ManMan Subscribe Service is an event-driven microservice that listens to RabbitMQ topics for manman worker and instance lifecycle events and sends formatted notifications to Slack.

## Overview

This service subscribes to the following topics:
- `worker.{id}.status-updates` - Worker lifecycle events
- `game-server-instance.{id}.status-updates` - Instance lifecycle events

## Features

- **Event Processing**: Handles worker and instance status changes (start, running, lost, crashed, complete)
- **Slack Integration**: Sends rich formatted messages with action buttons to Slack channels
- **Status Tracking**: Updates database status tracking for debugging and recovery scenarios
- **Recovery Handling**: Manages lost worker/instance recovery scenarios

## Usage

To start the subscribe service:

```bash
python -m friendly_computing_machine.cli.main bot subscribe \
  --rabbitmq-url "amqp://user:pass@localhost:5672/" \
  --slack-bot-token "xoxb-your-token-here" \
  --database-url "postgresql://user:pass@localhost/db"
```

## Environment Variables

The service can be configured using environment variables:

- `RABBITMQ_URL`: RabbitMQ connection URL
- `SLACK_WEB_API_TOKEN`: Slack Web API token for sending messages
- `DATABASE_URL`: PostgreSQL database connection URL

## Architecture

```
RabbitMQ Topics → ManMan Subscribe Service → Slack + Database
```

The service runs alongside the health server for monitoring and includes graceful shutdown handling.

## Current Status

This is currently a stub implementation. The following features need to be implemented:

- [ ] RabbitMQ connection and topic subscription
- [ ] Message processing and parsing
- [ ] Slack Web API integration
- [ ] Database status tracking
- [ ] Recovery scenario handling
- [ ] Action button handlers

## Related Documentation

See [manman_subscribe.md](../../../docs/manman_subscribe.md) for detailed requirements and architecture diagrams.
