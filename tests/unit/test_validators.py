from unittest.mock import AsyncMock, MagicMock

import dns.resolver
import pytest

from pulseroute.common.bot_detector import parse_user_agent
from pulseroute.common.email_validator import email_domain_accepts_mail

# --- Bot & User-Agent Detection ---

def test_googlebot_detection():
    ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    is_bot, device, browser, os_name = parse_user_agent(ua)
    assert is_bot is True


def test_iphone_detection():
    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    )
    is_bot, device, browser, os_name = parse_user_agent(ua)
    assert is_bot is False
    assert device == "mobile"
    assert os_name == "iOS"
    assert browser == "Safari"


# --- Email Domain DNS Validation ---

@pytest.mark.asyncio
async def test_accepts_domain_with_mx_record(monkeypatch):
    mock_resolve = AsyncMock(return_value=[MagicMock()])
    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", mock_resolve)
    assert await email_domain_accepts_mail("user@gmail.com") is True


@pytest.mark.asyncio
async def test_falls_back_to_a_record_when_no_mx(monkeypatch):
    async def mock_resolve(self, domain, qtype):
        if qtype == "MX":
            raise dns.resolver.NoAnswer()
        if qtype == "A":
            return [MagicMock()]
        raise dns.resolver.NXDOMAIN()

    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", mock_resolve)
    assert await email_domain_accepts_mail("user@a-record-only.com") is True


@pytest.mark.asyncio
async def test_rejects_nonexistent_domain(monkeypatch):
    mock_resolve = AsyncMock(side_effect=dns.resolver.NXDOMAIN())
    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", mock_resolve)
    assert await email_domain_accepts_mail("user@thisdomaindoesnotexistatall12345.com") is False


@pytest.mark.asyncio
async def test_fails_open_on_resolver_error(monkeypatch):
    mock_resolve = AsyncMock(side_effect=dns.resolver.Timeout())
    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", mock_resolve)
    assert await email_domain_accepts_mail("user@flaky-dns-server.com") is True
