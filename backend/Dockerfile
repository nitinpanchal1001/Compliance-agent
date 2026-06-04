FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

RUN pip install uv

WORKDIR /app

# ── deps layer (cached unless pyproject.toml changes) ──
FROM base AS deps
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev

# ── final image ────────────────────────────────────────
FROM base AS final
COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

EXPOSE 8000
