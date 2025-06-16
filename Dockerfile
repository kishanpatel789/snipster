FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim


WORKDIR /app
COPY pyproject.toml uv.lock README.md .

RUN uv sync --locked --no-install-project --no-dev

COPY ./src /app/src

CMD ["uv", "run", "fastapi", "run", "src/snipster/api.py", "--port", "80"]
