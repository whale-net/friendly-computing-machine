#/bin/bash

uv venv
source .venv/bin/activate
uv sync

if [ -e ".env" ]; then
    echo ".env file found"
    uv run --env-file .env fcm bot run
else
    echo "no .env file was found"
    uv run fcm bot run
fi