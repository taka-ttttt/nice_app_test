FROM ghcr.io/astral-sh/uv:0.9.2-python3.13-bookworm-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .
EXPOSE 8080
CMD ["uv", "run", "python", "src/main.py"]