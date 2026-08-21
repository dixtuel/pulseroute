<div align="center">

# PulseRoute

**Enterprise-Grade URL Shortener, Custom Domains & Real-Time Analytics Platform**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-pulseroute.onrender.com-00B4D8?style=flat&logo=render)](https://pulseroute.onrender.com)
[![CI Pipeline](https://github.com/dixtuel/pulseroute/actions/workflows/ci.yml/badge.svg)](https://github.com/dixtuel/pulseroute/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)

*Sub-10ms redirects, automated Caddy On-Demand TLS for custom domains, distributed Base62 ID generation, non-blocking Redis Stream analytics ingestion, GDPR/KVKK IP anonymization, and an embedded modern dashboard with rich terminal CLI.*

[🚀 Live Cloud Demo](https://pulseroute.onrender.com) • [Architecture](#system-architecture) • [Security & Privacy](#security-and-privacy) • [CLI Guide](#rich-terminal-cli) • [Production Deploy](#production-deployment-docker-compose)

---

</div>

## 🌐 Live Cloud Demo

PulseRoute is running live in production on Render with full Postgres & Redis backing:

👉 **[https://pulseroute.onrender.com](https://pulseroute.onrender.com)**

* **Live Telemetry Dashboard:** [pulseroute.onrender.com/dashboard](https://pulseroute.onrender.com/dashboard)
* **Interactive OpenAPI & Swagger Docs:** [pulseroute.onrender.com/docs](https://pulseroute.onrender.com/docs)
* **Health & Edge Diagnostics:** [pulseroute.onrender.com/healthz](https://pulseroute.onrender.com/healthz)

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

## ☁️ Cloud & Self-Hosted Deployment Options

PulseRoute adapts automatically to your environment — from a zero-config free demo to an enterprise distributed cluster:

### Option 1: 1-Click Free Cloud Deploy (Render Free Web Service)
PulseRoute includes built-in fallback drivers. When deployed on Render Free Tier without external services, it automatically operates in **Standalone Zero-Config Mode**:
* **Database:** Embedded SQLite (`sqlite+aiosqlite:///./pulseroute.db`).
* **Caching & Telemetry:** In-memory rate limiting and direct database click ingestion (no Redis required).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

### Option 2: 100% Free Persistent Cloud Setup (Render + Free Serverless DBs)
To make your Render free deployment completely persistent across container sleep/restarts, attach free cloud databases by adding 2 Environment Variables in your Render Dashboard:
1. **Free PostgreSQL (0.5 GB Free):** [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com)
   * Set `DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?ssl=require`
2. **Free Redis (10,000 commands/day Free):** [Upstash Serverless Redis](https://upstash.com)
   * Set `REDIS_URL=rediss://default:pass@xxx.upstash.io:6379`

---

### Option 3: Production Self-Hosted (Docker Compose)
Deploy the full enterprise stack (FastAPI + PostgreSQL 16 + Redis 7 + Caddy On-Demand TLS) in one command on your VPS:

```bash
git clone https://github.com/dixtuel/pulseroute.git
cd pulseroute/deploy
cp .env.example .env
docker compose up -d
```

---

## Testing & Quality Assurance

Run the comprehensive unit and integration test suite (21 passing tests):

```bash
# Run tests with coverage
pytest --cov=pulseroute -v

# Run linting
ruff check src/ tests/
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
