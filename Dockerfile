FROM openapitools/openapi-generator-cli:v7.13.0 as generator

WORKDIR /codegen
COPY ./external/manman-api.json /codegen/manman-api.json

# SUE ME not the same args as the script. may combine that one day, we'll see.
#RUN openapi-generator-cli generate \
RUN java -jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar \
    generate \
    -i /codegen/manman-api.json \
    -g python \
    -o /codegen/python-client \
    --skip-validate-spec \
    --additional-properties=packageName=external.manman_api

######

FROM python:3.11-slim as base
# not sure if it's necessary to pin uv for this project, but whatever may as well
# NOTE: update in github actions too
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

RUN mkdir /app/src
RUN mkdir /app/src/external
COPY --from=generator /codegen/python-client/external/* /app/src/external/manman_api/
RUN touch /app/src/external/__init__.py

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
#ENTRYPOINT ["sleep", "1000"]
ENTRYPOINT ["uv", "run", "opentelemetry-instrument", "fcm"]
