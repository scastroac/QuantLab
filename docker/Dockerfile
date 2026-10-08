ARG UV_VERSION=0.12.0
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=uv /uv /uvx /bin/
WORKDIR /app

COPY pyproject.toml uv.lock README.md .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
COPY config ./config
COPY plugins ./plugins
RUN uv sync --locked --no-dev

RUN groupadd --system quantlab \
    && useradd --system --gid quantlab --home-dir /app --no-create-home quantlab \
    && chown --recursive quantlab:quantlab /app

USER quantlab

CMD ["/app/.venv/bin/quantlab"]
