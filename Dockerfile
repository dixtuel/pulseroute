FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md MANIFEST.in .
COPY src/ src/
RUN pip install --no-cache-dir build && python -m build --wheel

FROM python:3.12-slim AS runner

WORKDIR /app

# Create a non-root unprivileged app user
RUN useradd -m -u 1000 appuser
USER appuser
ENV HOME=/home/appuser \
    PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

COPY --chown=appuser:appuser --from=builder /app/dist/*.whl .
RUN pip install --no-cache-dir --user *.whl && rm *.whl

EXPOSE 8000

CMD ["sh", "-c", "pulseroute serve --host 0.0.0.0 --port ${PORT:-8000}"]
