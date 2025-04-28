#/bin/bash

uv venv
source .venv/bin/activate
uv sync
uv run --env-file .env  fcm bot run