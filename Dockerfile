FROM python:3.12-slim


COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set work directory
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN uv sync

COPY . .

CMD ["uv", "run", "python", "bot.py"]
