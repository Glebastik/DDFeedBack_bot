FROM python:3.11-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /bot

RUN apt-get update && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости (слой кешируется отдельно от кода)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv pip install --system -r requirements.txt

# Копируем исходники
COPY . /bot

CMD ["python", "-m", "bot.main"]
