#!/bin/bash
# Exit script if any command fails
set -e

# --- Configuration ---
# assumes in external directory
SPEC_FILE="manman-api.json"
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


# Create the output directory
echo "Creating output directory $OUTPUT_DIR..."
mkdir -p "$OUTPUT_DIR"
# Define the temporary directory variable
OUTPUT_DIR_TMP="${OUTPUT_DIR}/.tmp_gen" # Temporary output directory *inside* final dir
# Create the temporary output directory
mkdir -p "$OUTPUT_DIR_TMP"

# --- Generate Code ---
echo "Generating Python client (version ${GENERATOR_VERSION}) from $SPEC_FILE..."
# Mount current directory (${PWD}) to /local inside the container
docker run --rm \
    -v "${PWD}/external:/localin" \
    -v "${PWD}/${OUTPUT_DIR_TMP}:/localout" \
    openapitools/openapi-generator-cli:${GENERATOR_VERSION} generate \
    -i "/localin/${SPEC_FILE}" \
    -g python \
    -o "/localout" \
    --additional-properties=packageName=external.${PACKAGE_NAME}

# change owner of the generated files to the current user
echo "Changing ownership of generated files to current user..."
sudo chown -R "$(id -u):$(id -g)" "${OUTPUT_DIR_TMP}"

echo "Moving generated code from tmp to $OUTPUT_DIR..."
# Move the contents of the generated package directory into the final output directory.
mv "${OUTPUT_DIR_TMP}/external/${PACKAGE_NAME}/"* "${OUTPUT_DIR}/"
# Remove the temporary directory
rm -rf "${OUTPUT_DIR_TMP}"

echo "-----------------------------------------------------"
echo "Client generation complete in: $OUTPUT_DIR"
echo "IMPORTANT: Make sure '$OUTPUT_DIR/' is in your .gitignore file!"
echo "-----------------------------------------------------"
