<div align="center">

# PulseRoute

**Self-hosted URL shortener with custom domains, click analytics, QR codes and webhooks**

[![CI Pipeline](https://github.com/dixtuel/pulseroute/actions/workflows/ci.yml/badge.svg)](https://github.com/dixtuel/pulseroute/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)

*Sub-10ms redirects, automated Caddy On-Demand TLS for custom domains, distributed Base62 ID generation, non-blocking Redis Stream analytics ingestion, GDPR/KVKK IP anonymization, and an embedded modern dashboard with rich terminal CLI.*

[Live Demo](https://ps.sely.tr) • [Architecture](#system-architecture) • [Security & Privacy](#security-and-privacy) • [CLI Guide](#rich-terminal-cli) • [Cloud Deploy](#cloud-deployment-render--neon--upstash) • [Self-Hosted Deploy](#self-hosted-deployment-docker-compose)

---

</div>

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
- **Multi-Tenant Workspace Isolation:** Every account gets its own workspace (`owner` role) on signup — there is no shared workspace. All link, analytics, custom-domain, and webhook endpoints require authentication and verify workspace membership before returning or mutating anything; anonymous links (24h TTL) have no owner and can't be managed via the API at all, only viewed in aggregate (`GET /api/v1/links/stats/anonymous-count`). In `REQUIRE_CUSTOM_DOMAIN=true` mode, anonymous link creation is rejected outright (server-side, and the dashboard now shows a "sign in required" state instead of the anonymous-link form) since anonymous visitors can never own a verified domain.
- **Brute-Force Protection:** Automated rate limiting and 10-minute IP jailing after 10 consecutive failed authentication attempts.
- **GDPR / KVKK Compliance:** Raw visitor IP addresses are never saved to disk. IPs are masked (`192.168.1.0/24`) prior to database persistence.
- **Data Encryption at Rest:** Webhook secrets are encrypted before being stored (Fernet: AES-128-CBC + HMAC-SHA256, keyed from `SECRET_KEY`) — never persisted or returned in plaintext after creation.
- **Custom Error Handling:** Branded 404/410/500 pages with support for custom fallback URLs per domain.
- **Single Platform AdSense Account:** Display-ad monetization is a single, server-administrator-configured account (`GLOBAL_ADSENSE_CLIENT_ID`/`GLOBAL_ADSENSE_SLOT_ID`) — Google AdSense requires per-site ownership verification, so per-user/per-workspace monetization isn't offered.

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

## Webhooks

Subscribe a workspace to `link.created` and/or `link.clicked` events (`POST /api/v1/webhooks`, workspace-scoped, auth required). Each event is delivered as a signed `POST`:

```
X-PulseRoute-Signature: <hmac-sha256(secret_key, body)>
```

The signing secret is generated server-side and shown exactly once in the creation response — verify the signature on your receiving endpoint before trusting the payload. This is API-only by design (no dashboard UI) to keep the web dashboard focused on the core shorten-a-link flow.

---

## Cloud Deployment (Render + Neon + Upstash)

The live instance at **[ps.sely.tr](https://ps.sely.tr)** runs this way — no server to manage, no card required on any of the three services:

1. **Web service:** deploy this repo to [Render](https://render.com) as a Python web service (`pip install -e .` / `pulseroute serve --host 0.0.0.0 --port $PORT`). Render's free plan needs no credit card; the default `*.onrender.com` subdomain can be disabled once your own custom domain is verified (Render dashboard → service → Settings → Custom Domains).
2. **Postgres:** create a free project on [Neon](https://neon.tech) (no card, no expiry) and set `DATABASE_URL` to its connection string — the app auto-normalizes `postgresql://...` to the `asyncpg` driver and strips query params `asyncpg` doesn't accept.
3. **Redis:** create a free database on [Upstash](https://upstash.com) (no card) and set `REDIS_URL` — the app auto-upgrades `redis://` to `rediss://` (TLS) for any `upstash.io` host.

That's the entire persistent, zero-cost stack; no Docker, no Caddy. Custom-domain TLS provisioning for *your own users'* domains (the `ALLOW_CUSTOM_DOMAINS` feature) still relies on Caddy's On-Demand TLS `ask` endpoint (see below) and isn't automatic on this cloud path — domains added there verify in the database, but a platform admin currently has to also add them as a Render custom domain by hand for traffic/TLS to actually route.

---

## Self-Hosted Deployment (Docker Compose)

Run the full stack (FastAPI + PostgreSQL 16 + Redis 7 + Caddy On-Demand TLS) with one command on your own server:

```bash
git clone https://github.com/dixtuel/pulseroute.git
cd pulseroute/deploy
cp .env.example .env
docker compose up -d
```

PulseRoute also ships with fallback drivers for a zero-infra local run: without `DATABASE_URL`/`REDIS_URL` set, it falls back to embedded SQLite and in-memory rate limiting — useful for trying it out, not for production.

---

## ⚙️ Configuration Reference

Full list with defaults lives in [`deploy/.env.example`](deploy/.env.example). The ones you're most likely to actually touch:

| Variable | Default | What it does |
| :--- | :--- | :--- |
| `DATABASE_URL` | embedded SQLite | Postgres connection string in production — see Docker Compose above. |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Cache + click-stream backend; omit entirely to run in zero-Redis fallback mode. |
| `PRIMARY_DOMAIN` | `localhost:8000` | The instance's own shared domain — used for short links when no custom domain is set, and as the CNAME/verification target for custom domains. Set this to your real deployed host (e.g. `links.example.com`). |
| `ALLOW_CUSTOM_DOMAINS` | `true` | Whether logged-in workspace owners/admins can add a custom domain at all. Set `false` to disable the feature entirely. |
| `REQUIRE_CUSTOM_DOMAIN` | `false` | `false` = shared-instance mode, everyone (anonymous included) can create links on `PRIMARY_DOMAIN`. `true` = bring-your-own-domain mode: link creation on the shared domain is disabled entirely, every workspace must add + verify its own domain first. |
| `ENFORCE_SAFE_BROWSING` | `true` | Rejects known-malicious/phishing destination URLs at link-creation time. |
| `ENFORCE_EMAIL_DOMAIN_CHECK` | `true` | Rejects registration if the email's domain has no MX/A record at all (catches typo/garbage domains). Fails open on DNS timeouts. |
| `OPERATOR_CONTACT_EMAIL` | unset | Shown (bot-obfuscated) on `/privacy` as the data-controller contact for this instance. |
| `GLOBAL_ADSENSE_CLIENT_ID` / `GLOBAL_ADSENSE_SLOT_ID` | unset | The single, server-wide Google AdSense unit shown on interstitial pages (see Security & Privacy above — this is not per-user). |
| `SECRET_KEY` | insecure placeholder | **Change this** in any real deployment — signs JWTs. |

Note: there is no per-user API key feature — JWT (`Authorization: Bearer <token>` from `/api/v1/auth/login`) is the only auth method.

---

## Testing & Quality Assurance

Run the comprehensive unit and integration test suite (34 passing tests):

```bash
# Run tests with coverage
pytest --cov=pulseroute -v

# Run linting
ruff check src/ tests/
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
