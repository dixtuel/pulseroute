from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from pulseroute.core.config import settings


def normalize_database_url(url: str) -> str:
    """Auto-normalizes standard postgresql:// URLs to asyncpg format and strips incompatible asyncpg query parameters."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if url.startswith("postgresql+asyncpg://") and "?" in url:
        parts = urlsplit(url)
        query_params = dict(parse_qsl(parts.query))

        # Remove query parameters that asyncpg.connect() does not accept
        for unsupported in ("channel_binding", "gssencmode", "target_session_attrs"):
            query_params.pop(unsupported, None)

        if "sslmode" in query_params:
            ssl_val = query_params.pop("sslmode")
            if ssl_val in ("require", "verify-ca", "verify-full"):
                query_params["ssl"] = "require"

        new_query = urlencode(query_params)
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    return url


db_url = normalize_database_url(settings.DATABASE_URL)

def get_engine_kwargs(url: str) -> dict:
    kwargs = {"echo": settings.DEBUG}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    elif "-pooler." in url or "neon.tech" in url:
        # Serverless / Neon pooler: PgBouncer handles connection pooling at the infrastructure layer (pool_mode=transaction).
        # Using NullPool prevents FastAPI from holding idle connections open,
        # which allows Neon compute to cleanly scale to zero when idle and avoid compute exhaustion.
        # Prepared statement caching must be disabled (0) for PgBouncer transaction mode compatibility to avoid duplicate statement errors.
        kwargs["poolclass"] = NullPool
        kwargs["connect_args"] = {
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
            "command_timeout": 30,
        }
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
        kwargs["pool_pre_ping"] = True
        kwargs["pool_recycle"] = 280  # Under Neon 300s scale-to-zero inactivity timeout
    return kwargs


engine_kwargs = get_engine_kwargs(db_url)
engine = create_async_engine(db_url, **engine_kwargs)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        link_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("short_links")}
        )
        moderation_backfill_needed = (
            "moderation_status" not in link_columns or "moderation_was_active" not in link_columns
        )
        for column, definition in (
            ("is_quarantined", "BOOLEAN DEFAULT FALSE"),
            ("quarantine_reason", "VARCHAR(255)"),
            ("abuse_reports_count", "INTEGER DEFAULT 0"),
            ("moderation_status", "VARCHAR(20) DEFAULT 'active' NOT NULL"),
            ("moderation_was_active", "BOOLEAN"),
            ("moderation_updated_at", "TIMESTAMP WITH TIME ZONE"),
        ):
            if column not in link_columns:
                await conn.execute(text(f"ALTER TABLE short_links ADD COLUMN {column} {definition}"))

        abuse_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("abuse_reports")}
        )
        reporter_fingerprint_missing = "reporter_fingerprint" not in abuse_columns
        if reporter_fingerprint_missing:
            await conn.execute(text("ALTER TABLE abuse_reports ADD COLUMN reporter_fingerprint VARCHAR(64)"))
        review_status_missing = "review_status" not in abuse_columns
        resolved_at_missing = "resolved_at" not in abuse_columns
        if review_status_missing:
            await conn.execute(
                text("ALTER TABLE abuse_reports ADD COLUMN review_status VARCHAR(20) DEFAULT 'new' NOT NULL")
            )
        if resolved_at_missing:
            await conn.execute(text("ALTER TABLE abuse_reports ADD COLUMN resolved_at TIMESTAMP WITH TIME ZONE"))

        if review_status_missing:
            await conn.execute(
                text(
                    "UPDATE abuse_reports SET review_status = CASE "
                    "WHEN status = 'dismissed' THEN 'rejected' "
                    "WHEN status IN ('resolved', 'deleted', 'removed') THEN 'approved' "
                    "ELSE 'new' END"
                )
            )
        if review_status_missing or resolved_at_missing:
            await conn.execute(
                text(
                    "UPDATE abuse_reports SET resolved_at = CURRENT_TIMESTAMP "
                    "WHERE review_status IN ('approved', 'rejected') AND resolved_at IS NULL"
                )
            )

        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_abuse_reports_review_page ON abuse_reports (review_status, id)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_abuse_reports_slug_fp ON abuse_reports (slug, reporter_fingerprint)")
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_short_links_moderation_id ON short_links (moderation_status, id)")
        )

        if moderation_backfill_needed:
            await conn.execute(
                text(
                    "UPDATE short_links SET moderation_status = "
                    "CASE WHEN moderation_status = 'active' THEN 'quarantined' ELSE moderation_status END, "
                    "moderation_was_active = FALSE WHERE is_quarantined = TRUE "
                    "AND (moderation_status = 'active' OR moderation_was_active IS NULL)"
                )
            )
