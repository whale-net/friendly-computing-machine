FROM python:3.11-alpine
# not sure if it's necessary to pin uv for this project, but whatever may as well
COPY --from=ghcr.io/astral-sh/uv:0.4.29 /uv /uvx /bin/

# Sync the project into a new environment, using the frozen lockfile
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

# install
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["uv", "run", "fcm"]
