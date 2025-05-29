# Development Container

This directory contains the configuration for a VS Code development container that provides a consistent development environment for the Friendly Computing Machine project.

## What's Included

- **Python 3.11** - Matches the project requirements
- **UV** - Package manager (version synchronized with Dockerfile)
- **Docker-in-Docker** - Required for external API client generation
- **Tilt** - Local development orchestration tool
- **Kind** - Local Kubernetes clusters for testing
- **Temporal CLI** - Command-line tool for Temporal workflows
- **Kubectl** - Kubernetes command-line tool
- **VS Code Extensions**:
  - Python language support
  - Pylint and Ruff for linting and formatting
  - Jupyter notebook support

## Setup

1. Open the project in VS Code
2. Install the "Dev Containers" extension if you haven't already
3. Command Palette → "Dev Containers: Reopen in Container"
4. Wait for the container to build and the setup script to complete

## What the Setup Does

The `setup.sh` script automatically:
1. Verifies UV installation (already included in base image)
2. Installs development tools (tilt, kind, kubectl, temporal cli)
3. Generates external API client dependencies 
4. Installs all project dependencies with `uv sync`
5. Verifies the installation works

## After Setup

Once the container is ready, you can:
- Run tests: `uv run pytest`
- Run the Slack bot: `uv run fcm bot run`
- Run the Temporal worker: `uv run workflow run`
- Use tilt for local development: `tilt up`
- Create a local kubernetes cluster: `kind create cluster`

## Local Kubernetes Development

To use tilt with a local Kubernetes cluster:
1. Create a kind cluster: `kind create cluster`
2. Switch kubectl context: `kubectl config use-context kind-kind`
3. Run tilt: `tilt up`

## Environment Variables

Remember to create a `.env` file with the required environment variables. See `.env.example` for the template.

## Pre-commit Hooks (Optional)

If you want to use pre-commit hooks:
```bash
uv add --dev pre-commit
uv run pre-commit install
```