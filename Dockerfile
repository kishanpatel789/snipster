FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim


WORKDIR /app
COPY pyproject.toml uv.lock README.md .

RUN uv sync --locked --no-install-project --no-dev

COPY ./src /app/src
COPY .env .

COPY ./scripts ./scripts

RUN PYTHONPATH=. uv run python scripts/seed_db.py

RUN rm -r ./scripts

CMD ["uv", "run", "fastapi", "run", "src/snipster/api.py", "--port", "80"]
