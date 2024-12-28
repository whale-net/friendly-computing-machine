FROM python:3.11-alpine
# not sure if it's necessary to pin uv for this project, but whatever may as well
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


# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# logging
ENV OTEL_SERVICE_NAME='friendly-computing-machine'
# auto logging is not desired
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=false
#ENV OTEL_LOGS_EXPORTER=console
ENV OTEL_TRACES_EXPORTER=otlp
# no metrics for now
ENV OTEL_METRICS_EXPORTER=none
## traffic is intended for within-pod. So hopefully this doesn't amtter
ENV OTEL_EXPORTER_OTLP_INSECURE=true

RUN uv run opentelemetry-bootstrap -a requirements | uv pip install --requirement -

#ENTRYPOINT ["uv", "run", "fcm"]
ENTRYPOINT ["uv", "run", "opentelemetry-instrument", "fcm"]
