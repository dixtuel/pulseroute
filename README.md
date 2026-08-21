<div align="center">

# PulseRoute

**Enterprise-Grade URL Shortener, Custom Domains & Real-Time Analytics Platform**

[![CI Pipeline](https://github.com/dixtuel/pulseroute/actions/workflows/ci.yml/badge.svg)](https://github.com/dixtuel/pulseroute/actions)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=dixtuel/pulseroute)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)

*Sub-10ms redirects, automated Caddy On-Demand TLS for custom domains, distributed Base62 ID generation, non-blocking Redis Stream analytics ingestion, GDPR/KVKK IP anonymization, and an embedded modern dashboard with rich terminal CLI.*

[Launch Instant Cloud Demo](#instant-cloud-demo-github-codespaces) • [Architecture](#system-architecture) • [Security & Privacy](#security-and-privacy) • [CLI Guide](#rich-terminal-cli) • [Production Deploy](#production-deployment-docker-compose)

---

</div>

## Overview

PulseRoute is an open-source link management and attribution platform built for developers, marketing teams, and infrastructure engineers who demand **complete data ownership**, **lightning-fast redirection speeds**, and **zero-friction custom domain onboarding**.

### Key Highlights:
- **Ultra-Fast Redirects (<10ms):** Redis Cache-Aside with Singleflight distributed locking and negative caching against cache stampede attacks.
- **Custom Domains & Zero-Config SSL:** Native Caddy On-Demand TLS integration (`/api/v1/internal/caddy-check`) with DNS TXT/CNAME validation.
- **Asynchronous Non-Blocking Analytics:** Ingests clicks instantly into Redis Streams (`XADD`), batch-consumed by async workers into PostgreSQL with GeoIP and Bot detection.
- **Geo & Device Targeting:** Automatically route by visitor country (e.g. Turkey -> Turkish site, US -> US site) or operating system (iOS -> App Store, Android -> Google Play).
- **Expired URL Fallback:** Gracefully redirect expired campaigns to custom fallback destinations instead of returning 404 errors.
- **GDPR & KVKK Compliance:** In-memory IP anonymization (truncates IPv4 last octet, hashes IPv6) and cookieless aggregate tracking.
- **Security Hardening:** AES-256 field-level encryption for sensitive credentials, brute-force login jail (15-min IP lockout), and strict Security Headers (HSTS, CSP, X-Frame-Options).
- **Rich Terminal CLI & Embedded Dashboard:** Control everything from a clean terminal UI or the included SPA web panel.

---

## Instant Cloud Demo (GitHub Codespaces)

You can launch and test the entire stack (FastAPI backend, Redis, SQLite/PostgreSQL, and Web Dashboard) directly in your browser with **zero local installation**:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=dixtuel/pulseroute)

1. Click the **Open in GitHub Codespaces** badge above.
2. The cloud container will automatically initialize dependencies, start the background workers, and open the interactive Web Dashboard in a new browser tab.
3. Access Swagger API documentation at `/docs` or control links via the integrated terminal with `pulseroute link create`.

---

## System Architecture

```mermaid
graph TD
    Client([Client / Visitor]) -->|HTTP Request /custom-domain/slug| Caddy[Caddy Proxy - On-Demand TLS]
    Caddy -->|Check Domain Auth| CaddyCheck[PulseRoute /api/v1/internal/caddy-check]
    Caddy -->|Forward Request| FastAPI[FastAPI Async Router]

    subgraph "Fast Read Path (<10ms)"
        FastAPI -->|1. Lookup Slug| RedisCache[(Redis KV Cache)]
        FastAPI -.->|Cache Miss| PG[(PostgreSQL / SQLite)]
    end

    FastAPI -->|HTTP 307 Redirect| Client

    subgraph "Non-Blocking Analytics Pipeline"
        FastAPI -->|2. Push Click Event| RedisStream[(Redis Stream `events:clicks`)]
        Worker[Async Batch Worker] -->|3. Consume 100-event Batches| RedisStream
        Worker -->|4. Anonymize IP + GeoIP + Bot Filter| Worker
        Worker -->|5. Bulk Insert| DBStore[(PostgreSQL Click Events)]
    end
```

---

## Security and Privacy

- **SQL Injection Prevention:** 100% parameterized queries via SQLAlchemy Async ORM.
- **Brute-Force Protection:** Automated rate limiting and 15-minute IP jailing after 5 consecutive failed authentication attempts.
- **GDPR / KVKK Compliance:** Raw visitor IP addresses are never saved to disk. IPs are masked (`192.168.1.0/24`) prior to database persistence.
- **Data Encryption at Rest:** Sensitive tokens and webhook secrets are encrypted with AES-256-GCM.
- **Custom Error Handling:** Branded 404/410/500 pages with support for custom fallback URLs per domain.

---

## Rich Terminal CLI

PulseRoute comes equipped with a first-class CLI powered by **Typer** and **Rich**:

```bash
# Start server and dashboard
pulseroute serve --port 8000

# Shorten a URL with custom slug and print an ASCII QR Code
pulseroute link create https://github.com/dixtuel/pulseroute --slug gh-repo --qr

# List all active links in a formatted table
pulseroute link list

# Add & verify custom domains
pulseroute domain add links.mybrand.com
pulseroute domain verify links.mybrand.com

# Inspect global analytics
pulseroute analytics summary --days 7
```

---

## Production Deployment (Docker Compose)

Deploy the full production stack (FastAPI + PostgreSQL + Redis + Caddy with automatic SSL) in one command:

```bash
git clone https://github.com/dixtuel/pulseroute.git
cd pulseroute/deploy
cp .env.example .env
docker compose up -d
```

---

## Testing & Quality Assurance

Run the comprehensive unit and integration test suite:

```bash
# Run tests with coverage
pytest --cov=pulseroute -v

# Run linting
ruff check src/ tests/
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
