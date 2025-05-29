# Development Container

This directory contains the configuration for a VS Code development container that provides a consistent development environment for the Friendly Computing Machine project.

## What's Included

- **Python 3.11** - Matches the project requirements
- **UV 0.5.13** - Package manager used by the project
- **Docker-in-Docker** - Required for external API client generation
- **VS Code Extensions**:
  - Python language support
  - Pylint and Ruff for linting
  - Black formatter
  - Jupyter notebook support

## Setup

1. Open the project in VS Code
2. Install the "Dev Containers" extension if you haven't already
3. Command Palette → "Dev Containers: Reopen in Container"
4. Wait for the container to build and the setup script to complete

## What the Setup Does

The `setup.sh` script automatically:
1. Installs UV 0.5.13
2. Generates external API client dependencies 
3. Installs all project dependencies with `uv sync`
4. Verifies the installation works

## After Setup

Once the container is ready, you can:
- Run tests: `uv run pytest`
- Run the Slack bot: `uv run fcm bot run`
- Run the Temporal worker: `uv run workflow run`

## Environment Variables

Remember to create a `.env` file with the required environment variables. See `.env.example` for the template.

## Pre-commit Hooks (Optional)

If you want to use pre-commit hooks:
```bash
uv add --dev pre-commit
uv run pre-commit install
```