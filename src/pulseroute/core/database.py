from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

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

# Engine configuration
engine_kwargs = {"echo": settings.DEBUG}
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10

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
