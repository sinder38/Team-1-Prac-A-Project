FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    FLASK_DEBUG=0

WORKDIR /app
COPY backend/ ./backend/
COPY data/ ./data/

WORKDIR /app/backend
RUN uv sync --frozen --no-dev \
    && mkdir -p /app/data/outputs

ENV PATH="/app/backend/.venv/bin:$PATH"

EXPOSE 5000
CMD ["python", "run_server.py"]
