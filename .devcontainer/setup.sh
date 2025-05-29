#!/bin/bash
set -e

echo "Setting up development environment..."

# Install UV (matching the version used in GitHub Actions and Dockerfile)
echo "Installing UV 0.5.13..."
curl -LsSf https://astral.sh/uv/0.5.13/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Verify UV installation
echo "UV version:"
uv --version

# Generate external dependencies
echo "Generating external API client..."
bash bin/generate_client.sh

# Install project dependencies
echo "Installing project dependencies..."
uv sync

# Verify the installation works
echo "Verifying installation..."
uv run python -c "import friendly_computing_machine; print('Project imported successfully')"

echo "Development environment setup complete!"
echo ""
echo "You can now:"
echo "  - Run tests: uv run pytest"
echo "  - Run the bot: uv run fcm bot run"
echo "  - Run temporal worker: uv run workflow run"
echo ""
echo "To set up pre-commit hooks (optional):"
echo "  - Install pre-commit: uv add --dev pre-commit"
echo "  - Install hooks: uv run pre-commit install"
echo ""
echo "Remember to set up your .env file with required environment variables."