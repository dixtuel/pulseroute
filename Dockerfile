FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md .
COPY src/ src/
RUN pip install --no-cache-dir build && python -m build --wheel

FROM python:3.12-slim AS runner

WORKDIR /app

# Create a non-root user for Hugging Face Spaces compatibility (user 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

WORKDIR /home/user/app

COPY --chown=user:user --from=builder /app/dist/*.whl .
RUN pip install --no-cache-dir --user *.whl && rm *.whl

EXPOSE 7860

CMD ["sh", "-c", "pulseroute serve --host 0.0.0.0 --port ${PORT:-7860}"]
