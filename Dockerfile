FROM ghcr.io/astral-sh/uv:0.11.32 AS uv
FROM python:3.13-slim
COPY --from=uv /uv /uvx /bin/
WORKDIR /code
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_DEV=1
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-install-project
COPY . .
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
