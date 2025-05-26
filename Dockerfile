FROM openapitools/openapi-generator-cli:v7.12.0 AS generator

WORKDIR /codegen
# Copy the entire external directory
COPY ./external /codegen/external

# Generate clients for all API specs using shell built-ins (no need for findutils)
RUN mkdir -p /codegen/src/external && \
    touch /codegen/src/external/__init__.py && \
    for spec_file in /codegen/external/*.json /codegen/external/*.yaml /codegen/external/*.yml; do \
        if [ -f "$spec_file" ]; then \
            package_name=$(basename "$spec_file" | sed 's/\.[^.]*$//' | tr '-' '_'); \
            echo "Generating client for $spec_file with package name: $package_name"; \
            java -jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar \
                generate \
                -i "$spec_file" \
                -g python \
                -o "/codegen/tmp_$package_name" \
                --skip-validate-spec \
                --additional-properties=packageName=external.$package_name; \
            mv "/codegen/tmp_$package_name/external/$package_name" "/codegen/src/external/$package_name"; \
            rm -rf "/codegen/tmp_$package_name"; \
        fi; \
    done

######

FROM python:3.11-slim AS base
# not sure if it's necessary to pin uv for this project, but whatever may as well
# NOTE: update in github actions too
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

RUN mkdir /app/src
RUN mkdir /app/src/external
# Copy all generated external packages
COPY --from=generator /codegen/src/external/ /app/src/external/

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# compile what already exists
RUN python -m compileall -f -o2 /app/src/external

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

RUN uv run opentelemetry-bootstrap -a requirements | uv pip install --requirement -

# Second phase: compile deps
RUN python -m compileall -f -o2 /app/.venv


# Third phase Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
#COPY . /app
COPY uv.lock pyproject.toml alembic.ini README.md /app/
COPY /src/friendly_computing_machine /app/src/friendly_computing_machine
COPY /src/migrations /app/src/migrations

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Fourth phase: compile app code
RUN python -m compileall -f -o2 /app/src

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# note: This service name is defined both here and in-code (cli callback).
# this will be overridden by the helm chart,
# but is set to a reasonable default here as well because it seems right
ENV OTEL_SERVICE_NAME='friendly-computing-machine'
# auto logging is not desired, see readme
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=false
#ENV OTEL_LOGS_EXPORTER=console
ENV OTEL_TRACES_EXPORTER=otlp
# no metrics for now
ENV OTEL_METRICS_EXPORTER=none
## traffic is intended for within-pod. So hopefully this doesn't amtter
ENV OTEL_EXPORTER_OTLP_INSECURE=true

# Disable bytecode compilation at runtime since we've already done it
ENV UV_COMPILE_BYTECODE=0

# testing installing this higher
# RUN uv run opentelemetry-bootstrap -a requirements | uv pip install --requirement -

#ENTRYPOINT ["uv", "run", "fcm"]
ENTRYPOINT ["uv", "run", "opentelemetry-instrument", "fcm"]
