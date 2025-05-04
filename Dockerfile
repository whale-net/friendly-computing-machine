FROM python:3.11-slim
# not sure if it's necessary to pin uv for this project, but whatever may as well
# NOTE: update in github actions too
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

    # Second phase: compile deps
RUN python -m compileall -f -o2 /app/.venv

# Third phase: generate client code from external spec
COPY external/manman-api.json /app/external/manman-api.json
# may not be best practice to copy the script in here, but it works
COPY bin/generate_client.sh /app/bin/generate_client.sh
RUN /app/bin/generate_client.sh

# Then, add the rest of the project source code and install it
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

RUN uv run opentelemetry-bootstrap -a requirements | uv pip install --requirement -

#ENTRYPOINT ["uv", "run", "fcm"]
ENTRYPOINT ["uv", "run", "opentelemetry-instrument", "fcm"]
