# ManMan Subscribe Service

The ManMan Subscribe Service is an event-driven microservice that listens to RabbitMQ topics for manman worker and instance lifecycle events and sends formatted notifications to Slack.

## Overview

This service subscribes to the following topics:
- `external.status.worker-instance.*` - Worker lifecycle events
- `external.status.game-server-instance.*` - Instance lifecycle events

## Features

- **Event Processing**: Handles worker and instance status changes (start, running, lost, crashed, complete)
- **Slack Integration**: Sends rich formatted messages with action buttons to Slack channels
- **Status Tracking**: Updates database status tracking for debugging and recovery scenarios

## Usage

just use tilt

## Environment Variables

read the cli entrypoint and callback


this had a bunch more shit but I deleted it because it was largely garbage
