#!/bin/bash
# Exit script if any command fails
set -e

# --- Configuration ---
# Adjust paths relative to the script's location (or project root)
SPEC_FILE="external/manman-api.json"
OUTPUT_DIR="src/external/manman_api"
# This is the package name the generator uses INTERNALLY for the generated code
# It should generally match the final directory name.
PACKAGE_NAME="manman_api"
# Pin the generator version for consistency!
GENERATOR_VERSION="v7.12.0"

# --- Preparation ---
# Ensure the parent directory for generated code exists
mkdir -p "$(dirname "$OUTPUT_DIR")"
# Ensure the parent 'external' directory is treated as a Python package
touch "src/external/__init__.py"
# # Ensure the 'src' directory is treated as a Python package
# touch "src/__init__.py"

# --- Clean Old Code ---
echo "Removing old generated code from $OUTPUT_DIR..."
rm -rf "$OUTPUT_DIR"
# Generator will create the output directory

# --- Generate Code ---
echo "Generating Python client (version ${GENERATOR_VERSION}) from $SPEC_FILE..."
# Mount current directory (${PWD}) to /local inside the container
docker run --rm \
    -v "${PWD}:/local" \
    openapitools/openapi-generator-cli:${GENERATOR_VERSION} generate \
    -i "/local/${SPEC_FILE}" \
    -g python \
    -o "/local/${OUTPUT_DIR}" \
    --additional-properties=packageName=${PACKAGE_NAME}

echo "-----------------------------------------------------"
echo "Client generation complete in: $OUTPUT_DIR"
echo "IMPORTANT: Make sure '$OUTPUT_DIR/' is in your .gitignore file!"
echo "-----------------------------------------------------"
