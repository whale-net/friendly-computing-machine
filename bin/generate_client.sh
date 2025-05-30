#!/bin/bash
# Exit script if any command fails
set -e

# --- Configuration ---
# Pin the generator version for consistency!
GENERATOR_VERSION="v7.12.0"
# Base directories
EXTERNAL_SPECS_DIR="external"
OUTPUT_BASE_DIR="src/external"

# Function to derive package name from spec file name
# Converts "some-api.json" or "some_api.yaml" to "some_api"
derive_package_name() {
    local spec_file="$1"
    # Remove file extension and convert hyphens to underscores
    basename "$spec_file" | sed 's/\.[^.]*$//' | tr '-' '_'
}

# Function to generate client for a single API spec
generate_client() {
    local spec_file="$1"
    local package_name="$2"
    local output_dir="$3"

    echo "=== Generating client for $spec_file ==="
    echo "Package name: $package_name"
    echo "Output directory: $output_dir"

    # Create the output directory
    echo "Creating output directory $output_dir..."
    mkdir -p "$output_dir"

    # Define the temporary directory variable
    local output_dir_tmp="${output_dir}/.tmp_gen"
    # Create the temporary output directory
    mkdir -p "$output_dir_tmp"

    # Generate Code
    echo "Generating Python client (version ${GENERATOR_VERSION}) from $spec_file..."
    # Mount current directory (${PWD}) to /local inside the container
    docker run --rm \
        -v "${PWD}/${EXTERNAL_SPECS_DIR}:/localin" \
        -v "${PWD}/${output_dir_tmp}:/localout" \
        openapitools/openapi-generator-cli:${GENERATOR_VERSION} generate \
        -i "/localin/$(basename "$spec_file")" \
        -g python \
        -o "/localout" \
        --additional-properties=packageName=external.${package_name}

    # Change owner of the generated files to the current user
    echo "Changing ownership of generated files to current user..."
    sudo chown -R "$(id -u):$(id -g)" "${output_dir_tmp}"

    echo "Moving generated code from tmp to $output_dir..."
    # Move the contents of the generated package directory into the final output directory.
    mv "${output_dir_tmp}/external/${package_name}/"* "${output_dir}/"
    # Remove the temporary directory
    rm -rf "${output_dir_tmp}"

    echo "Client generation complete for $package_name"
    echo ""
}

# --- Preparation ---
# Ensure the base output directory exists
echo "Setting up base directories..."
mkdir -p "$OUTPUT_BASE_DIR"
# Ensure the parent 'external' directory is treated as a Python package
touch "${OUTPUT_BASE_DIR}/__init__.py"

# --- Discovery and Generation ---
echo "Discovering API specification files in ${EXTERNAL_SPECS_DIR}/..."

# Find all API specification files (JSON, YAML, YML)
spec_files=$(find "$EXTERNAL_SPECS_DIR" -maxdepth 1 -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) | sort)

if [ -z "$spec_files" ]; then
    echo "ERROR: No API specification files found in ${EXTERNAL_SPECS_DIR}/"
    echo "Looking for files with extensions: .json, .yaml, .yml"
    exit 1
fi

echo "Found the following API specification files:"
echo "$spec_files"
echo ""

# Track generated packages for summary
generated_packages=()

# Generate client for each API specification
for spec_file in $spec_files; do
    # Derive package name from filename
    package_name=$(derive_package_name "$spec_file")
    output_dir="${OUTPUT_BASE_DIR}/${package_name}"

    # Clean old generated code for this specific package
    if [ -d "$output_dir" ]; then
        echo "Removing old generated code from $output_dir..."
        rm -rf "$output_dir"
    fi

    # Generate the client
    generate_client "$spec_file" "$package_name" "$output_dir"

    # Track this package
    generated_packages+=("$package_name")
done

# --- Summary ---
echo "=================================================="
echo "CLIENT GENERATION COMPLETE!"
echo "=================================================="
echo "Generated ${#generated_packages[@]} client package(s):"
for package in "${generated_packages[@]}"; do
    echo "  - external.${package} (in ${OUTPUT_BASE_DIR}/${package}/)"
done
echo ""
echo "IMPORTANT NOTES:"
echo "1. Make sure '${OUTPUT_BASE_DIR}/*/' is in your .gitignore file!"
echo "2. Import clients like: from external.${generated_packages[0]} import ApiClient"
echo "3. Each package is independent and can be used separately."
echo "=================================================="
