import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from pulseroute.core.config import settings
from pulseroute.core.database import Base, get_db
from pulseroute.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # Registration tests use made-up domains (company.com, competitor.com, ...) -- don't hit
    # real DNS in the test suite; the email-domain-check logic itself is unit-tested separately.
    orig_email_check = settings.ENFORCE_EMAIL_DOMAIN_CHECK
    settings.ENFORCE_EMAIL_DOMAIN_CHECK = False

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    settings.ENFORCE_EMAIL_DOMAIN_CHECK = orig_email_check


async def override_get_db():
    async with test_session_maker() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with test_session_maker() as session:
        yield session
