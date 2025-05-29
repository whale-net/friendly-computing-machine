#!/bin/bash
set -e

echo "Setting up development environment..."

# UV is already installed in the base image, just verify
echo "UV version:"
uv --version

# Install development tools
echo "Installing development tools..."

# Install tilt
echo "Installing tilt..."
curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash

# Install kind for local kubernetes
echo "Installing kind..."
# For AMD64 / x86_64
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.26.0/kind-linux-amd64
# For ARM64
[ $(uname -m) = aarch64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.26.0/kind-linux-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Install kubectl
echo "Installing kubectl..."
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv ./kubectl /usr/local/bin/kubectl

# Install temporal cli
echo "Installing temporal cli..."
wget https://github.com/temporalio/cli/releases/latest/download/temporal_cli_linux_amd64.tar.gz
tar -xzf temporal_cli_linux_amd64.tar.gz
sudo mv temporal /usr/local/bin/
rm temporal_cli_linux_amd64.tar.gz

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
echo "  - Use tilt for local development: tilt up"
echo "  - Create a local kubernetes cluster: kind create cluster"
echo "  - Use temporal cli: temporal"
echo ""
echo "To set up pre-commit hooks (optional):"
echo "  - Install pre-commit: uv add --dev pre-commit"
echo "  - Install hooks: uv run pre-commit install"
echo ""
echo "To set up local kubernetes for tilt:"
echo "  - Create cluster: kind create cluster"
echo "  - Switch kubectl context: kubectl config use-context kind-kind"
echo ""
echo "Remember to set up your .env file with required environment variables."