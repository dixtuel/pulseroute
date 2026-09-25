<div align="center">

# PulseRoute

**A self-hosted link shortener with custom domains, analytics and a small, focused dashboard.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)

[Live demo](https://ps.sely.tr) · [Quick start](#quick-start) · [Configuration](#configuration) · [Development](#development)

---

</div>

## What it does

- Create short links, QR codes, custom domains and workspaces.
- View click analytics and publish signed `link.created` / `link.clicked` webhooks.
- Route browsers through a fixed five-second verification screen; API clients and bots receive a redirect directly. Link creators cannot change the delay.
- Accept abuse reports and provide an owner-only moderation desk for reports, restricted links and appeals.
- Use the English or Turkish dashboard. The default follows the browser language (`tr`/`az` → Turkish; otherwise English).

FastAPI serves the application. PostgreSQL stores accounts, links and moderation records; Redis provides cache and a bounded click-event stream. Redis is not a replacement for the database, and buffered analytics can be lost if its Redis service loses data.

## Security and privacy

- Workspace APIs check membership before reading or changing account-owned data. Anonymous links expire after 24 hours and cannot be managed through an account API.
- Visitor IP addresses are masked before analytics storage. Abuse and moderation records use the documented retention policy in the application.
- Webhook secrets are encrypted at rest using a key derived from `SECRET_KEY`.
- The private owner desk is disabled unless both moderation owner settings are configured.

## CLI

Install the package, then use the `pulseroute` command:

```bash
pulseroute serve --port 8000
pulseroute link create https://example.com --slug example --qr
pulseroute link list
pulseroute domain add links.example.com
pulseroute domain verify links.example.com
pulseroute analytics summary --days 7
```

## Quick start

Run the included FastAPI, PostgreSQL, Redis and Caddy stack with Docker Compose:

```bash
git clone https://github.com/dixtuel/pulseroute.git
cd pulseroute/deploy
docker compose up --build -d
```

Open the dashboard at `http://localhost:8000/dashboard`. The Compose file uses local PostgreSQL and Redis defaults. Set production secrets and domain values in the `app` service environment before exposing the service publicly. The app can also be deployed to a Python web host with an external PostgreSQL database and any compatible Redis provider; see [`deploy/.env.example`](deploy/.env.example) for available settings.

The shared-domain live instance is [ps.sely.tr](https://ps.sely.tr). Custom-domain TLS for a self-hosted deployment uses the included Caddy `ask` endpoint.

## Configuration

See [`deploy/.env.example`](deploy/.env.example) for settings and defaults. The main production settings are:

| Variable | Purpose |
| :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string. Local development defaults to SQLite. |
| `REDIS_URL` | Redis-compatible cache and rate-limit backend. |
| `ANALYTICS_REDIS_URL` | Optional Redis-compatible click-event stream backend; defaults to `REDIS_URL`. Redis is temporary queue/cache storage, not the database. |
| `SECRET_KEY` | Signs JWTs and derives encryption keys. Set a unique, random secret for every deployment. |
| `PRIMARY_DOMAIN` | Shared link host for this instance. |
| `ALLOW_CUSTOM_DOMAINS` / `REQUIRE_CUSTOM_DOMAIN` | Enable user domains and choose shared-domain or bring-your-own-domain link creation. |
| `MODERATION_OWNER_EMAIL` | Optional owner login email. |
| `MODERATION_OWNER_PASSWORD_HASH` | Optional bcrypt hash for the owner password; never set the plaintext password. |

The owner login can also sign in through the regular dashboard if the same email belongs to an active database account. It does not bypass PostgreSQL availability or create that account. Moderation thresholds and retention policy are fixed in code.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
npm ci
npm run build:css
pulseroute serve --reload
```

Tailwind utility CSS is compiled to `src/pulseroute/web/static/tailwind.css`; Node.js is only needed to regenerate this file after changing utility classes. Run the tests with `pytest` and lint with `ruff check src/ tests/`.

## API and webhooks

The JSON API is rooted at `/api/v1`. Webhook subscriptions are workspace-scoped and require authentication. Deliveries include an HMAC signature:

```
X-PulseRoute-Signature: <hmac-sha256(secret_key, body)>
```

The signing secret is returned once when the subscription is created. Verify the signature before trusting a webhook payload.

## Open-source attribution

See [`ATTRIBUTION.md`](ATTRIBUTION.md) for external libraries and services used by PulseRoute.

## License

PulseRoute is licensed under the [MIT License](LICENSE).
